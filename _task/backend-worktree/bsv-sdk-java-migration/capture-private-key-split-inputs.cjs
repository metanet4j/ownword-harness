// 固定 PrivateKey.split.test.ts 的原输入：私钥随机、Shamir 拆分的随机多项式与 x 坐标、
// 备份串转换与恢复。
// 随机入口按原语言的 getRandomValues 观察形状记录实际字节（kind: entropy），
// 熵流来自既有固定熵记录（Java 侧 Replay 用同一份字节），保证两侧逐次同键。
// toBackupShares/fromBackupShares 只是同一文件里两个可注入原语的薄封装，
// 探针登记的是实际消耗熵的 toKeyShares 与 toBackupFormat。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_PRIVATE_KEY_SPLIT_TS_OBSERVATIONS
if (!output) throw new Error('缺少 PrivateKey.split 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/primitives/PrivateKey.ts')
const fixturePath = path.join(__dirname, 'metanet4j-bsv-sdk/src/test/resources/keys-private-public-random-replay-20260926.txt')

const occurrences = new Map()
const entropyCache = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let queue = []
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/PrivateKey\.split\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('PrivateKey.split 入口缺少固定原测试调用位置')
  return Number(match[1])
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('PrivateKey.split 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
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
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw',
    name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function number (value) { return { kind: 'number', value: String(value) } }
function argument (value) {
  if (value === undefined || value === null) return { kind: 'undefined' }
  if (typeof value === 'number') return number(value)
  return { kind: 'string', value: String(value) }
}
function string (value) { return { kind: 'string', value: String(value) } }
function stringArray (value) { return { kind: 'stringArray', value: Array.from(value, item => String(item)) } }
function privateKey (value) { return { kind: 'privateKey', hex: value.toHex() } }
function keyShares (value) {
  return { kind: 'keyShares', threshold: value.threshold, integrity: value.integrity,
    points: value.points.map(point => String(point)) }
}

// 原测试的随机来自既有固定熵记录：两侧必须逐次同键。
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
      if (queue.length === 0) return Reflect.apply(source.getRandomValues, source, [array])
      const next = queue.shift()
      if (next.length !== array.length) throw new Error('固定原测试熵长度不符：' + current())
      array.set(next)
      record('random', [], { kind: 'entropy', length: array.length, bytesHex: hex(next) })
      return array
    }
  })
  Object.defineProperty(globalThis, 'crypto', { configurable: true, value: patched })
}

installEntropy()

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  if (!entropyCache.has(sourceFile)) entropyCache.set(sourceFile, loadEntropy(sourceFile))
  queue = (entropyCache.get(sourceFile).get(test) || []).slice()
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  const Original = moduleObject.default
  const Shares = moduleObject.KeyShares
  const originals = {
    fromRandom: Original.fromRandom,
    fromKeyShares: Original.fromKeyShares,
    toKeyShares: Original.prototype.toKeyShares,
    toBackupFormat: Shares.prototype.toBackupFormat,
    fromBackupFormat: Shares.fromBackupFormat,
    toWif: Original.prototype.toWif
  }
  Original.fromRandom = function (...args) {
    return observe('fromRandom', [], () => Reflect.apply(originals.fromRandom, this, args), privateKey)
  }
  Original.fromKeyShares = function (...args) {
    return observe('fromKeyShares', [keyShares(args[0])],
      () => Reflect.apply(originals.fromKeyShares, this, args), privateKey)
  }
  Original.prototype.toKeyShares = function (...args) {
    return observe('toKeyShares', [argument(args[0]), argument(args[1])],
      () => Reflect.apply(originals.toKeyShares, this, args), keyShares)
  }
  Shares.prototype.toBackupFormat = function (...args) {
    return observe('toBackupFormat', [], () => Reflect.apply(originals.toBackupFormat, this, args), stringArray)
  }
  Shares.fromBackupFormat = function (...args) {
    return observe('fromBackupFormat', [stringArray(args[0])],
      () => Reflect.apply(originals.fromBackupFormat, this, args), keyShares)
  }
  Original.prototype.toWif = function (...args) {
    return observe('toWif', [], () => Reflect.apply(originals.toWif, this, args), string)
  }
  return moduleObject
})
