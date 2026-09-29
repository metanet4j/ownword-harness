// 固定原文件：src/primitives/__tests/BigNumber.constructor.test.ts
// 原测试不改写；只记录真实 API 调用、原断言实参和循环内的每次执行。
const fs = require('node:fs')
const path = require('node:path')
const nativeExpect = global.expect
const output = process.env.MIGRATION_BN_OBSERVATIONS
if (!output) throw new Error('缺少 MIGRATION_BN_OBSERVATIONS')
const testPath = nativeExpect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const modulePath = path.join(sdk, 'src/primitives/BigNumber.ts')
let Original
let calls = []
let depth = 0
const occurrences = new Map()

function value(input) {
  if (input === undefined) return { type: 'undefined' }
  if (input === null) return { type: 'null' }
  if (typeof input === 'number') {
    const bytes = Buffer.alloc(8)
    bytes.writeDoubleBE(input)
    return { type: 'number', bits: bytes.toString('hex') }
  }
  if (typeof input === 'string') return { type: 'string', value: input }
  if (Array.isArray(input)) return { type: 'array', value: input.map(value) }
  if (input instanceof Original) return { type: 'BigNumber' }
  throw new Error('未支持的采集类型：' + typeof input)
}

function observe(method, args, action) {
  if (depth !== 0) return action()
  const call = { method, args: args.map(value) }
  depth++
  try {
    const result = action()
    call.outcome = { kind: 'return', value: value(result) }
    return result
  } catch (error) {
    call.outcome = { kind: 'throw', name: error.name, message: error.message }
    throw error
  } finally {
    depth--
    calls.push(call)
  }
}

// 延迟到原测试导入时安装，保持上游 ts-jest 的首个编译入口不变。
jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  Original = moduleObject.default
  moduleObject.default = new Proxy(Original, {
    construct(target, args) { return observe('constructor', args, () => Reflect.construct(target, args)) }
  })
  for (const method of ['toString', 'toNumber', 'toArray']) {
    const original = Original.prototype[method]
    jest.spyOn(Original.prototype, method).mockImplementation(function (...args) {
      return observe(method, args, () => Reflect.apply(original, this, args))
    })
  }
  const words = Object.getOwnPropertyDescriptor(Original.prototype, 'words').get
  jest.spyOn(Original.prototype, 'words', 'get').mockImplementation(function () {
    return observe('words', [], () => Reflect.apply(words, this, []))
  })
  return moduleObject
})

global.expect = Object.assign(function (actual) {
  const location = new Error().stack.match(/\/BigNumber\.constructor\.test\.ts:(\d+):\d+/)
  if (!location) throw new Error('未找到原断言位置')
  const line = Number(location[1])
  let actualOutcome = typeof actual === 'function' ? null : { kind: 'return', value: value(actual) }
  const argument = typeof actual === 'function' ? () => {
    try {
      const result = actual()
      actualOutcome = { kind: 'return', value: value(result) }
      return result
    } catch (error) {
      actualOutcome = { kind: 'throw', name: error.name, message: error.message }
      throw error
    }
  } : actual
  const assertion = nativeExpect(argument)
  return new Proxy(assertion, { get(target, matcher) {
    if (!['toEqual', 'toThrow', 'toBeLessThan'].includes(matcher)) throw new Error('未支持的原断言：' + String(matcher))
    return (...args) => {
      try { return Reflect.apply(target[matcher], target, args) }
      finally {
        const test = nativeExpect.getState().currentTestName
        const key = test + ':' + line
        const occurrence = (occurrences.get(key) ?? 0) + 1
        occurrences.set(key, occurrence)
        fs.appendFileSync(output, JSON.stringify({ test, line, occurrence, calls, matcher, actual: actualOutcome }) + '\n')
        calls = []
      }
    }
  } })
}, nativeExpect)
