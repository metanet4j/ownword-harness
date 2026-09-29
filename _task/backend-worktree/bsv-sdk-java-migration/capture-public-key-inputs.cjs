// 全量运行分派表按字面量识别本局部的输出环境变量：process.env.MIGRATION_PUBLIC_KEY_TS_OBSERVATIONS
// 固定 PublicKey.test.ts 与 PublicKey.additional.test.ts：只记录原测试直接发起的
// PublicKey 构造与公开方法调用。两个原文件共用同一份包装实现（装载顺序决定哪个探针
// 实例赢得 jest.doMock 注册），因此本文件在两个局部里内容完全相同。
// 原测试的随机私钥来自固定熵回放（Java 侧 Replay 用同一份记录字节），
// 因此以私钥/公钥实际值作输入即可同时证明两侧的前置状态一致。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

// 原文件 → 本文件负责的入口轨迹环境变量。
const LEDGERS = {
  'src/primitives/__tests/PublicKey.test.ts': 'MIGRATION_PUBLIC_KEY_TS_OBSERVATIONS',
  'src/primitives/__tests/PublicKey.additional.test.ts': 'MIGRATION_PUBLIC_KEY_ADDITIONAL_TS_OBSERVATIONS'
}
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const publicKeyPath = path.join(sdk, 'src/primitives/PublicKey.ts')
const fixturePath = path.join(__dirname, 'metanet4j-bsv-sdk/src/test/resources/keys-private-public-random-replay-20260926.txt')
const occurrenceMap = new Map()
const entropyCache = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false
let queue = []

function current () { return expect.getState().currentTestName }
/** 当前原文件是本次探测负责的两个文件之一时返回其路径，否则返回 null。 */
function ownedFile () {
  const observed = expect.getState().testPath
  if (typeof observed !== 'string') return null
  for (const file of Object.keys(LEDGERS)) if (observed.endsWith('/' + file)) return file
  return null
}
function ledgerPath (file) {
  const value = process.env[LEDGERS[file]]
  return value === undefined ? null : value
}
function callLine () {
  const file = ownedFile()
  if (file === null) return null
  const name = file.slice(file.lastIndexOf('/') + 1).replace(/\./g, '\\.')
  const match = new Error().stack.match(new RegExp(name + ':(\\d+):\\d+'))
  return match ? Number(match[1]) : null
}
/** 模块加载期的固定调用与其他原文件都不进入账本。 */
function record (method, args, result, line = callLine()) {
  const test = current()
  const file = ownedFile()
  if (!test || file === null) return false
  const output = ledgerPath(file)
  if (output === null) return false
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file, line }, method, args, result }) + '\n')
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
function bigNumber (value) { return { kind: 'bigNumber', value: String(value) } }
function string (value) { return { kind: 'string', value } }
function boolean (value) { return { kind: 'boolean', value: Boolean(value) } }
function encoding (value) { return value === undefined || value === null ? { kind: 'undefined' } : string(value) }
function bytes (value) {
  const list = Uint8Array.from(value)
  return { kind: 'numberArray', length: list.length, hex: hex(list) }
}
function privateKey (value) { return { kind: 'privateKey', hex: hex(value.toArray('be', 32)) } }
function publicKey (value) { return { kind: 'publicKey', hex: value.toString() } }
function point (value) {
  if (value === null || value === undefined) return { kind: 'null' }
  if (value.isInfinity()) return { kind: 'point', infinity: true }
  return { kind: 'point', x: String(value.getX()), y: String(value.getY()) }
}
function signature (value) { return { kind: 'signature', r: String(value.r), s: String(value.s) } }
function callback (value) { return typeof value === 'function' ? { kind: 'function' } : { kind: 'undefined' } }
function prefix (value) {
  if (value === undefined || value === null) return { kind: 'undefined' }
  return typeof value === 'string' ? string(value) : bytes(value)
}
function message (value) {
  if (typeof value === 'string') return string(value)
  return bigNumber(value)
}
function outcome (value) {
  return typeof value === 'string' ? string(value) : bytes(value)
}

function loadEntropy (file) {
  // 固定熵记录先给出 @id/原文件/用例全名 头部，再按 id 排列字节行。
  const names = new Map()
  const groups = new Map()
  for (const line of fs.readFileSync(fixturePath, 'utf8').split('\n')) {
    if (line === '' || line.startsWith('#')) continue
    const fields = line.split('\t')
    if (fields[0].startsWith('@')) {
      names.set(fields[0].substring(1), fields[1] + '\t' + fields[2])
      continue
    }
    const identity = names.get(fields[0])
    if (identity === undefined || !identity.startsWith(path.basename(file) + '\t')) continue
    const name = identity.slice(identity.indexOf('\t') + 1)
    if (!groups.has(name)) groups.set(name, [])
    groups.get(name).push(Uint8Array.from(Buffer.from(fields[2], 'hex')))
  }
  return groups
}

function installEntropy () {
  const source = globalThis.crypto
  const patched = Object.create(source)
  Object.defineProperty(patched, 'getRandomValues', {
    value (array) {
      // 非本探测负责的原文件与测试之外（Jest 自身）仍走真实随机源。
      if (!current() || ownedFile() === null) return Reflect.apply(source.getRandomValues, source, [array])
      const next = queue.shift()
      if (next === undefined) throw new Error('固定原测试熵流不足：' + current())
      if (next.length !== array.length) throw new Error('固定原测试熵长度不符：' + current())
      array.set(next)
      return array
    }
  })
  Object.defineProperty(globalThis, 'crypto', { configurable: true, value: patched })
  beforeEach(() => {
    const file = ownedFile()
    if (file === null) {
      queue = []
      return
    }
    if (!entropyCache.has(file)) entropyCache.set(file, loadEntropy(file))
    queue = (entropyCache.get(file).get(current()) || []).slice()
  })
}

installEntropy()

beforeEach(() => {
  const test = current()
  occurrence = (occurrenceMap.get(test) || 0) + 1
  occurrenceMap.set(test, occurrence)
  sequence = 0
})

jest.doMock(publicKeyPath, () => {
  const moduleObject = jest.requireActual(publicKeyPath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  const Original = moduleObject.default
  const originals = {
    fromPrivateKey: Original.fromPrivateKey,
    fromString: Original.fromString,
    fromDER: Original.fromDER,
    fromMsgHashAndCompactSignature: Original.fromMsgHashAndCompactSignature
  }
  Original.fromPrivateKey = function (...args) {
    return observe('fromPrivateKey', [privateKey(args[0])],
      () => Reflect.apply(originals.fromPrivateKey, this, args), publicKey)
  }
  Original.fromString = function (...args) {
    return observe('fromString', [string(args[0])],
      () => Reflect.apply(originals.fromString, this, args), publicKey)
  }
  Original.fromDER = function (...args) {
    return observe('fromDER', [bytes(args[0])],
      () => Reflect.apply(originals.fromDER, this, args), publicKey)
  }
  Original.fromMsgHashAndCompactSignature = function (...args) {
    const list = [bigNumber(args[0]), typeof args[1] === 'string' ? string(args[1]) : bytes(args[1])]
    if (args[2] !== undefined && args[2] !== null) list.push(string(args[2]))
    return observe('fromMsgHashAndCompactSignature', list,
      () => Reflect.apply(originals.fromMsgHashAndCompactSignature, this, args), publicKey)
  }
  const prototype = Original.prototype
  const methods = {}
  for (const name of ['deriveSharedSecret', 'verify', 'toDER', 'toHash', 'toAddress', 'deriveChild']) {
    methods[name] = prototype[name]
  }
  prototype.deriveSharedSecret = function (...args) {
    return observe('deriveSharedSecret', [privateKey(args[0])],
      () => Reflect.apply(methods.deriveSharedSecret, this, args), point)
  }
  prototype.verify = function (...args) {
    return observe('verify', [message(args[0]), signature(args[1]), encoding(args[2])],
      () => Reflect.apply(methods.verify, this, args), value => boolean(value))
  }
  prototype.toDER = function (...args) {
    return observe('toDER', [encoding(args[0])],
      () => Reflect.apply(methods.toDER, this, args), outcome)
  }
  prototype.toHash = function (...args) {
    return observe('toHash', [encoding(args[0])],
      () => Reflect.apply(methods.toHash, this, args), outcome)
  }
  prototype.toAddress = function (...args) {
    return observe('toAddress', [prefix(args[0])],
      () => Reflect.apply(methods.toAddress, this, args), string)
  }
  prototype.deriveChild = function (...args) {
    return observe('deriveChild',
      [privateKey(args[0]), string(args[1]), callback(args[2]), callback(args[3])],
      () => Reflect.apply(methods.deriveChild, this, args), publicKey)
  }
  const ProxyClass = new Proxy(Original, {
    construct (target, args, newTarget) {
      return observe('constructor', args.map(value => {
        if (value === null || value === undefined) return { kind: 'null' }
        if (typeof value === 'string') return string(value)
        if (typeof value === 'number') return { kind: 'number', value: String(value) }
        if (typeof value === 'boolean') return boolean(value)
        if (value instanceof Original) return publicKey(value)
        // 只有 Point 形状的对象才会走到这里；不提前 require 源文件，避免影响源文件转换配置。
        if (value !== null && typeof value === 'object' && typeof value.getX === 'function') return point(value)
        return bigNumber(value)
      }), () => Reflect.construct(target, args, newTarget), publicKey)
    }
  })
  return { ...moduleObject, __esModule: true, default: ProxyClass }
})
