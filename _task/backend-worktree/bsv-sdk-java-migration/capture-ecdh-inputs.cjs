// 固定 ECDH.test.ts：随机源只登记原测试可复现的字节，ECDH 结果登记共享密钥字符串。
// PrivateKey／PublicKey 互相引用，因此用真实模块、只包装原测试直接调用的静态与原型方法。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_ECDH_TS_OBSERVATIONS
if (!output) throw new Error('缺少 ECDH 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = 'src/primitives/__tests/ECDH.test.ts'
const privateKeyPath = path.join(sdk, 'src/primitives/PrivateKey.ts')
const publicKeyPath = path.join(sdk, 'src/primitives/PublicKey.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let privateKeyNamespace = null

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/ECDH\.test\.ts:(\d+):\d+/)
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
/** mock 工厂可能被调用多次；同一命名空间只包装一次，避免叠加包装。 */
function patch (holder, name, factory) {
  if (holder[name] && holder[name].__probeWrapped === true) return
  const original = holder[name]
  const wrapped = factory(original)
  wrapped.__probeWrapped = true
  Object.defineProperty(holder, name, { value: wrapped, writable: true, configurable: true, enumerable: false })
}

// 随机源：TS Random(32) 的返回是 0..255 的字节，Java 侧按同一数组重建密钥。
function bytes (value) { return { kind: 'array', value: Array.from(value, item => ({ type: 'number', value: String(item) })) } }
// ECDH 共享密钥是 Point；两侧的 Point.toString() 都是压缩编码 hex，逐字节可复现。
function hex (value) { return { kind: 'string', value: String(value) } }

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(privateKeyPath, () => {
  const moduleObject = jest.requireActual(privateKeyPath)
  if (privateKeyNamespace === null && moduleObject.default !== undefined) {
    patch(moduleObject.default, 'fromRandom', original => function (...args) {
      return observe('fromRandom', [], () => Reflect.apply(original, this, args),
        key => bytes(key.toArray()))
    })
    // 原测试的共享密钥入口是 PrivateKey.deriveSharedSecret（它直接调用 PublicKey.mulCT），
    // 因此按原型方法登记结果；返回的 Point.toString() 两侧都是压缩编码 hex。
    patch(moduleObject.default.prototype, 'deriveSharedSecret', original => function (...args) {
      return observe('deriveSharedSecret', [], () => Reflect.apply(original, this, args), hex)
    })
    privateKeyNamespace = moduleObject
  }
  return privateKeyNamespace === null ? moduleObject : privateKeyNamespace
})

// PublicKey 只作为参数被构造和校验，原测试没有直接发起它的公开入口；
// 保留一次 doMock 以确保 PrivateKey 的共享密钥派生走同一个真实模块实例。
jest.doMock(publicKeyPath, () => jest.requireActual(publicKeyPath))
