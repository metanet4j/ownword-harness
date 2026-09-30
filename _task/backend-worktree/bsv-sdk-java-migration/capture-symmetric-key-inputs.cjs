// 固定 SymmetricKey.test.ts：只记录原测试直接发起的加密/解密入口。
// 随机 IV 使密文本身不可跨语言逐值比较，因此密文只登记来源与长度；
// 固定向量与固定密文的解密输入仍逐字节登记。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_SYMMETRIC_KEY_TS_OBSERVATIONS
if (!output) throw new Error('缺少 SymmetricKey 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
// 探针作为 setup 文件会在同一次运行的每个原文件环境里各加载一次；
// 只有本探测负责的原文件才登记入口，其余环境只放行不记录。
const sourceFile = 'src/primitives/__tests/SymmetricKey.test.ts'
const modulePath = path.join(sdk, 'src/primitives/SymmetricKey.ts')
const occurrences = new Map()
const produced = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/SymmetricKey\.test\.ts:(\d+):\d+/)
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

function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function toBytes (value, enc) {
  if (typeof value === 'string') return Uint8Array.from(Buffer.from(value, enc === 'hex' ? 'hex' : 'utf8'))
  return Uint8Array.from(value)
}
function encoding (enc) { return enc === undefined || enc === null ? { kind: 'undefined' } : { kind: 'string', value: enc } }
function plaintext (value, enc) {
  const bytes = toBytes(value, enc)
  return { kind: 'plaintext', length: bytes.length, hex: hex(bytes) }
}
function ciphertext (value, enc) {
  const bytes = toBytes(value, enc)
  if (produced.has(hex(bytes))) return { kind: 'ciphertext', length: bytes.length, origin: 'encrypt' }
  return { kind: 'ciphertext', length: bytes.length, hex: hex(bytes) }
}
function outcome (value) {
  if (typeof value === 'string') return { kind: 'string', value }
  const bytes = Uint8Array.from(value)
  return { kind: 'numberArray', length: bytes.length, hex: hex(bytes) }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  produced.clear()
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  const Original = moduleObject.default
  const originalEncrypt = Original.prototype.encrypt
  const originalDecrypt = Original.prototype.decrypt
  Original.prototype.encrypt = function (...args) {
    return observe('encrypt', [plaintext(args[0], args[1]), encoding(args[1])],
      () => Reflect.apply(originalEncrypt, this, args), value => {
        const bytes = toBytes(value, undefined)
        produced.set(hex(bytes), true)
        return { kind: 'ciphertext', length: bytes.length }
      })
  }
  Original.prototype.decrypt = function (...args) {
    return observe('decrypt', [ciphertext(args[0], args[1]), encoding(args[1])],
      () => Reflect.apply(originalDecrypt, this, args), outcome)
  }
  return moduleObject
})
