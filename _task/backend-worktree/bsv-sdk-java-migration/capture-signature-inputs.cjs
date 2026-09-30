// 固定 Signature.test.ts 原输入：fromDER/fromCompact/verify/toDER/toCompact 与恢复入口。
// 随机输入用固定资源文件里的同一批 PrivateKey.fromRandom 字节重放，两侧才是同输入。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_SIGNATURE_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Signature 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/primitives/Signature.ts')
const randomPath = path.join(sdk, 'src/primitives/Random.ts')
const fixturePath = path.join(__dirname, 'metanet4j-bsv-sdk/src/test/resources/keys-ecdsa-random-fixture.properties')
// 固定 TS 实测随机字节：与 Java 测试共用同一份 keys-ecdsa-random-fixture.properties。
const RANDOM_FIXTURE = [
  ['verifies a valid signature against a string message', ['verifyValid']],
  ['returns false for a wrong signature', ['verifyWrongSigner', 'verifyWrongOther']],
  ['verifies with hex encoding', ['verifyHex']],
  ['recovers the public key from a signature', ['recover']],
  ['returns a valid recovery factor for a known key/msg pair', ['factorValid']],
  ['throws when no valid recovery factor can be found', ['factorWrongSigner', 'factorWrongOther']]
]
const fixture = new Map()
for (const line of fs.readFileSync(fixturePath, 'utf8').split('\n')) {
  const text = line.trim()
  if (text === '' || text.startsWith('#')) continue
  const separator = text.indexOf('=')
  fixture.set(text.slice(0, separator), text.slice(separator + 1))
}
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false
let queue = []
let queued = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/Signature\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('Signature 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
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
function number (value) {
  return { kind: 'number', value: Number.isInteger(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER ? value : String(value) }
}
function describeBytes (value) { return { kind: 'bytes', hex: hex(Uint8Array.from(value)) } }
function describeData (data) {
  return typeof data === 'string' ? { kind: 'string', value: data } : describeBytes(data)
}
function describeSignature (signature) {
  return { kind: 'signature', r: signature.r.toString(16), s: signature.s.toString(16) }
}
function describePublicKey (key) { return { kind: 'bytes', hex: hex(Uint8Array.from(key.encode(true))) } }
function describeBigNumber (value) { return { kind: 'bignumber', hex: value.toString(16) } }
function describeEncoding (enc) { return enc === undefined || enc === null ? [] : [{ kind: 'string', value: enc }] }
function receiver (signature) { return { kind: 'receiver', value: describeSignature(signature) } }
function describeEncoded (result) {
  return typeof result === 'string' ? { kind: 'string', value: result } : describeBytes(result)
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  const entry = RANDOM_FIXTURE.find(([suffix]) => test.endsWith(suffix))
  queued = entry !== undefined
  queue = queued ? [...entry[1]] : []
})

function install (Original) {
  const originals = {}
  for (const method of ['toDER', 'toString', 'toCompact', 'verify', 'RecoverPublicKey', 'CalculateRecoveryFactor']) {
    originals[method] = Original.prototype[method]
  }
  for (const method of ['fromDER', 'fromCompact']) originals[method] = Original[method]

  Original.fromDER = function (...args) {
    return observe('fromDER', [describeData(args[0]), ...describeEncoding(args[1])],
      () => Reflect.apply(originals.fromDER, this, args), describeSignature)
  }
  Original.fromCompact = function (...args) {
    return observe('fromCompact', [describeData(args[0]), ...describeEncoding(args[1])],
      () => Reflect.apply(originals.fromCompact, this, args), describeSignature)
  }
  Original.prototype.toDER = function (...args) {
    return observe('toDER', [receiver(this), ...describeEncoding(args[0])],
      () => Reflect.apply(originals.toDER, this, args), describeEncoded)
  }
  Original.prototype.toString = function (...args) {
    return observe('toString', [receiver(this), ...describeEncoding(args[0])],
      () => Reflect.apply(originals.toString, this, args), describeEncoded)
  }
  Original.prototype.toCompact = function (...args) {
    const compressed = typeof args[1] === 'boolean'
      ? { kind: 'boolean', value: args[1] } : { kind: 'string', value: String(args[1]) }
    return observe('toCompact', [receiver(this), number(args[0]), compressed, ...describeEncoding(args[2])],
      () => Reflect.apply(originals.toCompact, this, args), describeEncoded)
  }
  Original.prototype.verify = function (...args) {
    return observe('verify', [receiver(this), { kind: 'string', value: String(args[0]) },
        describePublicKey(args[1]), ...describeEncoding(args[2])],
      () => Reflect.apply(originals.verify, this, args), result => ({ kind: 'boolean', value: result }))
  }
  Original.prototype.RecoverPublicKey = function (...args) {
    return observe('RecoverPublicKey', [receiver(this), number(args[0]), describeBigNumber(args[1])],
      () => Reflect.apply(originals.RecoverPublicKey, this, args), describePublicKey)
  }
  Original.prototype.CalculateRecoveryFactor = function (...args) {
    return observe('CalculateRecoveryFactor', [receiver(this), describePublicKey(args[0]), describeBigNumber(args[1])],
      () => Reflect.apply(originals.CalculateRecoveryFactor, this, args), result => number(result))
  }
}

// Signature 与 Transaction／ECDSA 互相引用：只包装原型与静态方法，且只安装一次。
jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  install(moduleObject.default)
  return moduleObject
})

// PrivateKey.fromRandom() 的熵：按固定资源文件重放，保证两侧私钥逐字节相同。
jest.doMock(randomPath, () => {
  const moduleObject = jest.requireActual(randomPath)
  const wrapped = (length) => {
    if (!queued) {
      process.stderr.write('Signature 探针：未登记随机输入的用例 ' + current() + '\n')
      return moduleObject.default(length)
    }
    if (length !== 32) throw new Error('固定 TS 随机输入长度不是 32：' + current())
    const name = queue.shift()
    if (name === undefined) throw new Error('固定 TS 随机输入次数多于登记：' + current())
    const value = fixture.get(name)
    if (value === undefined) throw new Error('固定 TS 随机输入缺少条目：' + name)
    return Array.from(Buffer.from(value, 'hex'))
  }
  return { ...moduleObject, __esModule: true, default: wrapped }
})
