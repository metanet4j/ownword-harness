// 固定 ECIES.test.ts：只记录原测试直接发起的 ECIES 静态入口。
// bitcoreEncrypt 的 IV 与临时发送方私钥都随机，密文不逐值比较，只登记来源与长度；
// electrumEncrypt 在给定发送方私钥时完全确定，密文逐字节登记。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_ECIES_TS_OBSERVATIONS
if (!output) throw new Error('缺少 ECIES 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
// 探针作为 setup 文件会在同一次运行的每个原文件环境里各加载一次；
// 只有本探测负责的原文件才登记入口，其余环境只放行不记录。
const sourceFile = 'src/compat/__tests/ECIES.test.ts'
const modulePath = path.join(sdk, 'src/compat/ECIES.ts')
const occurrences = new Map()
const produced = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false
let entropyCounter = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/ECIES\.test\.ts:(\d+):\d+/)
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
function bytes (value) {
  const list = Uint8Array.from(value)
  return { kind: 'bytes', length: list.length, hex: hex(list) }
}
function privateKey (value) {
  if (value === null || value === undefined) return { kind: 'undefined' }
  return { kind: 'privateKey', hex: hex(value.toArray('be', 32)) }
}
function publicKey (value) {
  if (value === null || value === undefined) return { kind: 'undefined' }
  return { kind: 'publicKey', hex: value.toString() }
}
function boolean (value) { return { kind: 'boolean', value: Boolean(value) } }
/** 随机 IV／随机临时密钥产生的密文只登记来源和长度。 */
function cipher (value, deterministic) {
  const list = Uint8Array.from(value)
  produced.set(hex(list), deterministic)
  return deterministic ? { kind: 'bytes', length: list.length, hex: hex(list) }
    : { kind: 'bytes', length: list.length, origin: 'random' }
}
function cipherInput (value) {
  const list = Uint8Array.from(value)
  const deterministic = produced.get(hex(list))
  if (deterministic === undefined) return { kind: 'bytes', length: list.length, hex: hex(list) }
  return deterministic ? { kind: 'bytes', length: list.length, hex: hex(list) }
    : { kind: 'bytes', length: list.length, origin: 'random' }
}
function outcome (value) {
  const list = Uint8Array.from(value)
  return { kind: 'bytes', length: list.length, hex: hex(list) }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  produced.clear()
  entropyCounter = 0
})

// bitcoreEncrypt 的 IV、临时发送方私钥与 PrivateKey.fromRandom 都来自 SDK 的 Random；
// 探针把熵源固定为可重放字节并逐次登记，Java 侧用 CompatRandom.setSource 消费同一份字节。
function installEntropy () {
  const source = globalThis.crypto
  const patched = Object.create(source)
  Object.defineProperty(patched, 'getRandomValues', {
    value (array) {
      if (!current() || !mine()) return Reflect.apply(source.getRandomValues, source, [array])
      entropyCounter += 1
      array.fill(1)
      array[array.length - 1] = 0x10 + (entropyCounter % 0xef)
      const bytes = Uint8Array.from(array)
      record('random', [{ kind: 'number', value: String(bytes.length) }],
        { kind: 'bytes', length: bytes.length, hex: hex(bytes) })
      return array
    }
  })
  Object.defineProperty(globalThis, 'crypto', { configurable: true, value: patched })
}

installEntropy()

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  const Original = moduleObject.default
  const originals = {
    bitcoreEncrypt: Original.bitcoreEncrypt,
    bitcoreDecrypt: Original.bitcoreDecrypt,
    electrumEncrypt: Original.electrumEncrypt,
    electrumDecrypt: Original.electrumDecrypt
  }
  // 唯一没有模块入口的原用例是 expect(ECIES).toBeDefined()：断言取值时才会调用该字符串表示。
  // JS 的 String(类) 是源码文本，Java 侧同类观察只能是 [object Object]，因此统一规范为该占位值。
  Object.defineProperty(Original, 'toString', {
    configurable: true,
    value: function () {
      record('moduleExport', [{ kind: 'export', name: 'ECIES' }], { kind: 'string', value: '[object Object]' })
      return '[object Object]'
    }
  })

  Original.bitcoreEncrypt = function (...args) {
    return observe('bitcoreEncrypt',
      [bytes(args[0]), publicKey(args[1]), privateKey(args[2])],
      () => Reflect.apply(originals.bitcoreEncrypt, this, args),
      value => cipher(value, false))
  }
  Original.bitcoreDecrypt = function (...args) {
    return observe('bitcoreDecrypt', [cipherInput(args[0]), privateKey(args[1])],
      () => Reflect.apply(originals.bitcoreDecrypt, this, args), outcome)
  }
  Original.electrumEncrypt = function (...args) {
    const deterministic = args[2] !== undefined && args[2] !== null
    return observe('electrumEncrypt',
      [bytes(args[0]), publicKey(args[1]), privateKey(args[2]), boolean(args[3])],
      () => Reflect.apply(originals.electrumEncrypt, this, args),
      value => cipher(value, deterministic))
  }
  Original.electrumDecrypt = function (...args) {
    return observe('electrumDecrypt', [cipherInput(args[0]), privateKey(args[1]), publicKey(args[2])],
      () => Reflect.apply(originals.electrumDecrypt, this, args), outcome)
  }
  return moduleObject
})
