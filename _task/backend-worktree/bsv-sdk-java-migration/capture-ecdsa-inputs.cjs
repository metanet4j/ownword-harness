// 固定 ECDSA.test.ts：只记录原测试直接发起的 ECDSA 公开入口与 Point 原型运算。
// ECDSA 与 Point 互相引用，因此用真实模块只包装模块导出与 Point 原型方法。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_ECDSA_TS_OBSERVATIONS
if (!output) throw new Error('缺少 ECDSA 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
// 探针作为 setup 文件会在同一次运行的每个原文件环境里各加载一次；
// 只有本探测负责的原文件才登记入口，其余环境只放行不记录。
const sourceFile = 'src/primitives/__tests/ECDSA.test.ts'
const ecdsaPath = path.join(sdk, 'src/primitives/ECDSA.ts')
const pointPath = path.join(sdk, 'src/primitives/Point.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let ecdsaProxy = null
let installedPoint = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/ECDSA\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
/** 只登记本探针负责的原测试文件；同一次 Jest 运行里的其他原文件不属于本账本。 */
function mine () {
  const observed = expect.getState().testPath
  return typeof observed === 'string' && observed.endsWith('/' + sourceFile)
}
/** 模块加载期的固定调用不属于任何原用例，不进入账本。 */
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test || !mine()) return false
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
  return true
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function observe (method, args, action, describe) {
  if (depth !== 0) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? null : describe(result))
    return result
  } catch (error) {
    record(method, args, thrown(error))
    throw error
  } finally {
    depth--
  }
}

function bigNumber (value) { return { kind: 'bigNumber', value: String(value) } }
function boolean (value) { return { kind: 'boolean', value: Boolean(value) } }
// 判断无穷远点时必须走未被包装的原方法，否则描述函数会再次进入包装器。
let originalIsInfinity = null
function isInfinite (value) { return Reflect.apply(originalIsInfinity, value, []) }
function point (value) {
  if (isInfinite(value)) return { kind: 'point', infinity: true }
  return { kind: 'point', x: String(value.getX()), y: String(value.getY()) }
}
function signature (value) { return { kind: 'signature', r: String(value.r), s: String(value.s) } }
function signArgs (args) {
  const list = [bigNumber(args[0]), bigNumber(args[1]), boolean(args[2])]
  if (args[3] !== undefined && args[3] !== null) list.push(bigNumber(args[3]))
  return list
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(ecdsaPath, () => {
  const moduleObject = jest.requireActual(ecdsaPath)
  if (ecdsaProxy !== null) return ecdsaProxy
  // ECDSA 是命名空间导入：导出按属性读取；ECDSA 与 Signature 互相引用，
  // 构造 mock 时命名导出可能尚未填充，因此原函数必须在调用时再解析。
  const namespace = moduleObject
  function original (name) {
    const holder = typeof namespace[name] === 'function' ? namespace
      : (namespace.default && typeof namespace.default[name] === 'function' ? namespace.default : null)
    if (holder === null) {
      throw new Error('无法解析 ECDSA 原导出：' + name + '；' + Reflect.ownKeys(Object(namespace)).join(','))
    }
    return holder[name]
  }
  const wrappedSign = function (...args) {
    return observe('sign', signArgs(args), () => Reflect.apply(original('sign'), this, args), signature)
  }
  const wrappedVerify = function (...args) {
    return observe('verify',
      [bigNumber(args[0]), signature(args[1]), point(args[2])],
      () => Reflect.apply(original('verify'), this, args), value => ({ kind: 'boolean', value }))
  }
  // 包装后的入口必须由工厂返回的模块对象提供。
  ecdsaProxy = new Proxy(namespace, {
    get (target, property) {
      if (property === 'sign') return wrappedSign
      if (property === 'verify') return wrappedVerify
      return Reflect.get(target, property)
    }
  })
  return ecdsaProxy
})

jest.doMock(pointPath, () => {
  const moduleObject = jest.requireActual(pointPath)
  if (installedPoint || moduleObject.default === undefined) return moduleObject
  installedPoint = true
  const Original = moduleObject.default
  const originals = {
    mul: Original.prototype.mul,
    add: Original.prototype.add,
    neg: Original.prototype.neg,
    isInfinity: Original.prototype.isInfinity
  }
  originalIsInfinity = originals.isInfinity
  Original.prototype.mul = function (...args) {
    return observe('mul', [{ kind: 'receiver', point: point(this) }, bigNumber(args[0])],
      () => Reflect.apply(originals.mul, this, args), point)
  }
  Original.prototype.add = function (...args) {
    return observe('add', [{ kind: 'receiver', point: point(this) }, point(args[0])],
      () => Reflect.apply(originals.add, this, args), point)
  }
  Original.prototype.neg = function (...args) {
    return observe('neg', [{ kind: 'receiver', point: point(this) }],
      () => Reflect.apply(originals.neg, this, args), point)
  }
  Original.prototype.isInfinity = function (...args) {
    return observe('isInfinity', [{ kind: 'receiver', point: point(this) }],
      () => Reflect.apply(originals.isInfinity, this, args), value => ({ kind: 'boolean', value }))
  }
  return moduleObject
})
