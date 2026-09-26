// 只记录固定原测试直接执行的真实入口；内部计算和断言格式化不计为输入。
'use strict'
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.MIGRATION_POINT_ADDITIONAL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Point 输入输出路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const testFileName = path.basename(testPath)
const jacobian = testFileName === 'JacobianPoint.test.ts'
const classes = {}
let BN, Point, JPoint, bnString, pointX, pointY, toP
let sequence = 0
let depth = 0
let occurrence = 0
const occurrences = new Map()
beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})
function encode (item) {
  if (item === undefined) return { type: 'undefined' }
  if (item === null) return { type: 'null' }
  if (['string', 'boolean', 'number'].includes(typeof item)) return { type: typeof item, value: item }
  if (item instanceof BN) return { type: 'BigNumber', hex: bnString.call(item, 16) }
  if (item instanceof Point) return item.inf
    ? { type: 'Point', infinity: true }
    : { type: 'Point', infinity: false, x: bnString.call(pointX.call(item), 16), y: bnString.call(pointY.call(item), 16) }
  if (item instanceof JPoint) {
    if (!jacobian) return { type: 'JacobianPoint', affine: encode(toP.call(item)) }
    return { type: 'JacobianPoint', x: bnString.call(item.x.fromRed(), 16),
      y: bnString.call(item.y.fromRed(), 16), z: bnString.call(item.z.fromRed(), 16), zOne: item.zOne }
  }
  if (typeof item === 'function') return { type: 'function', name: item.name }
  if (Array.isArray(item)) return { type: 'array', value: item.map(encode) }
  if (Object.getPrototypeOf(item) === Object.prototype) {
    return { type: 'object', value: Object.fromEntries(Object.keys(item).sort().map(key => [key, encode(item[key])])) }
  }
  throw new Error('未表征的原输入类型：' + item.constructor?.name)
}
function source () {
  const first = new Error().stack.split('\n').slice(2).find(frame =>
    !frame.includes('capture-point-additional-inputs.cjs') && !frame.includes('/node_modules/jest-mock/'))
  if (!first?.includes(testFileName + ':')) return null
  const match = first.match(/:(\d+):\d+\)?$/)
  return { file: sourceFile, line: Number(match[1]) }
}
function call (method, receiver, args, action) {
  const site = depth === 0 ? source() : null
  depth++
  try {
    if (site && expect.getState().currentTestName) {
      fs.appendFileSync(output, JSON.stringify({ test: expect.getState().currentTestName, occurrence,
        sequence: ++sequence, method, receiver: encode(receiver), args: args.map(encode), source: site }) + '\n')
    }
    if (jacobian && method === 'JacobianPoint.mixedAdd' && args[0] &&
        Object.getPrototypeOf(args[0]) === Object.prototype && typeof args[0].isInfinity === 'function') {
      const object = args[0]
      const original = object.isInfinity
      const wrapped = function (...callbackArgs) {
        const result = Reflect.apply(original, this, callbackArgs)
        fs.appendFileSync(output, JSON.stringify({ test: expect.getState().currentTestName, occurrence,
          sequence: ++sequence, method: 'PointLike.isInfinity', receiver: encode(null),
          args: callbackArgs.map(encode), result: encode(result), source: site }) + '\n')
        return result
      }
      Object.defineProperty(wrapped, 'name', { value: original.name })
      object.isInfinity = wrapped
      try { return action() } finally { object.isInfinity = original }
    }
    return action()
  } finally { depth-- }
}
const methods = {
  Point: ['getX', 'getY', 'isInfinity', 'validate', 'toJSON', 'encode', 'inspect', 'add', 'dbl', 'neg',
  'dblp', 'mul', 'mulCT', 'mulAdd', 'jmulAdd', 'eq', 'toJ', '_getDoubles', '_combineWnafPair', '_collectWnafStep'],
  BigNumber: ['toArray', 'toString', 'eq', 'neg', 'addn'],
  JacobianPoint: ['toP', 'isInfinity', 'neg', 'add', 'mixedAdd', 'dbl', 'dblp', 'eq', 'eqXToP', 'inspect']
}
// 延迟至原测试导入，保持固定 ts-jest 的原编译入口。
let loading = false
jest.doMock(path.join(sdk, 'src/primitives/Point.ts'), () => {
  if (loading) return jest.requireActual(path.join(sdk, 'src/primitives/Point.ts'))
  loading = true
  for (const name of ['Point', 'BigNumber', 'JacobianPoint']) {
    const filename = path.join(sdk, 'src/primitives/' + name + '.ts')
    classes[name] = { filename, module: jest.requireActual(filename) }
    classes[name].type = classes[name].module.default
  }
  BN = classes.BigNumber.type; Point = classes.Point.type; JPoint = classes.JacobianPoint.type
  bnString = BN.prototype.toString; pointX = Point.prototype.getX; pointY = Point.prototype.getY
  toP = JPoint.prototype.toP
  let pointModule
for (const [name, info] of Object.entries(classes)) {
  for (const method of methods[name]) {
    const original = info.type.prototype[method]
    if (typeof original !== 'function') throw new Error('缺少原方法：' + name + '.' + method)
    jest.spyOn(info.type.prototype, method).mockImplementation(function (...args) {
      return call(name + '.' + method, this, args, () => Reflect.apply(original, this, args))
    })
  }
  const proxy = new Proxy(info.type, {
    construct (target, args, newTarget) {
      return call(name + '.constructor', null, args, () => Reflect.construct(target, args, newTarget))
    },
    get (target, key, receiver) {
      if (key === 'toString') return target.toString.bind(target)
      const value = Reflect.get(target, key, receiver)
      if (typeof value !== 'function' || key === 'prototype') return value
      return (...args) => call(name + '.' + String(key), null, args, () => Reflect.apply(value, target, args))
    }
  })
  const module = { ...info.module, default: proxy, __esModule: true }
  if (name === 'Point') pointModule = module
  else jest.doMock(info.filename, () => module)
}
  return pointModule
})
