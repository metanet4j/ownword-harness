// 固定 SymmetricKeyCompatibility.test.ts 的原输入：只登记原测试真实发起的私钥／公钥／对称密钥入口。
// 结果按原语言实际观察形状记录：私钥与公钥是十六进制字符串，对称密钥是十进制字符串，
// 解密结果是明文或异常。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_SYMMETRIC_KEY_COMPATIBILITY_TS_OBSERVATIONS
if (!output) throw new Error('缺少 SymmetricKeyCompatibility 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const privateKeyPath = path.join(sdk, 'src/primitives/PrivateKey.ts')
const symmetricKeyPath = path.join(sdk, 'src/primitives/SymmetricKey.ts')

const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let privateKeyInstalled = false
let symmetricKeyInstalled = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/SymmetricKeyCompatibility\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('SymmetricKeyCompatibility 入口缺少固定原测试调用位置')
  return Number(match[1])
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('SymmetricKeyCompatibility 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function observe (method, args, action, describe) {
  if (depth !== 0) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? outcome(result) : describe(result))
    return result
  } catch (error) {
    record(method, args, thrown(error))
    throw error
  } finally {
    depth--
  }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function string (value) { return { kind: 'string', value: String(value) } }
function encoding (value) { return value === undefined || value === null ? { kind: 'undefined' } : string(value) }
function numberArray (value) {
  const list = Uint8Array.from(value)
  return { kind: 'numberArray', length: list.length, hex: hex(list) }
}
function privateKey (value) { return { kind: 'privateKey', hex: value.toHex() } }
function publicKey (value) { return { kind: 'publicKey', hex: value.toString() } }
function symmetricKey (value) { return { kind: 'symmetricKey', value: String(value) } }
function outcome (value) {
  if (typeof value === 'string') return string(value)
  if (value === undefined || value === null) return { kind: 'undefined' }
  return numberArray(value)
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw',
    name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(privateKeyPath, () => {
  const moduleObject = jest.requireActual(privateKeyPath)
  if (privateKeyInstalled || moduleObject.default === undefined) return moduleObject
  privateKeyInstalled = true
  const Original = moduleObject.default
  const originals = { fromWif: Original.fromWif, toPublicKey: Original.prototype.toPublicKey }
  Original.fromWif = function (...args) {
    return observe('fromWif', [string(args[0])], () => Reflect.apply(originals.fromWif, this, args), privateKey)
  }
  Original.prototype.toPublicKey = function (...args) {
    return observe('toPublicKey', [], () => Reflect.apply(originals.toPublicKey, this, args), publicKey)
  }
  return moduleObject
})

jest.doMock(symmetricKeyPath, () => {
  const moduleObject = jest.requireActual(symmetricKeyPath)
  if (symmetricKeyInstalled || moduleObject.default === undefined) return moduleObject
  symmetricKeyInstalled = true
  const Original = moduleObject.default
  const decryptOriginal = Original.prototype.decrypt
  Original.prototype.decrypt = function (...args) {
    return observe('decrypt', [numberArray(args[0]), encoding(args[1])],
      () => Reflect.apply(decryptOriginal, this, args), outcome)
  }
  const ProxyClass = new Proxy(Original, {
    construct (target, args, newTarget) {
      return observe('constructor', [numberArray(args[0])], () => Reflect.construct(target, args, newTarget),
        symmetricKey)
    }
  })
  return { ...moduleObject, __esModule: true, default: ProxyClass }
})
