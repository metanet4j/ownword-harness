// 固定 PrivateKey.test.ts 的原输入：BRC42 派生、hex/string 往返转换与 10,000 次随机转换。
// 10,000 次循环的随机熵来自既有固定熵记录（Java 侧 Replay 用同一份字节，两侧必须逐次同键），
// 但输入样本只登记前三次迭代（循环站点结构覆盖），其余迭代的断言仍按每次执行登记。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_PRIVATE_KEY_TS_OBSERVATIONS
if (!output) throw new Error('缺少 PrivateKey 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/primitives/PrivateKey.ts')
const fixturePath = path.join(__dirname, 'metanet4j-bsv-sdk/src/test/resources/keys-private-public-random-replay-20260926.txt')
const LOOP_TEST = 'PrivateKey PrivateKey Validation and Conversion Tests 10,000 random private keys for valid conversions'
const LOOP_SAMPLES = 3

const occurrences = new Map()
const entropyCache = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let iterations = 0
let queue = []
let installed = false
let toHexOriginal = null

function current () { return expect.getState().currentTestName }
/** 10,000 次循环只登记前 LOOP_SAMPLES 次迭代的入口；其他原用例全部登记。 */
function recording () { return current() !== LOOP_TEST || iterations <= LOOP_SAMPLES }
function entropyActive () { return current() === LOOP_TEST && iterations <= LOOP_SAMPLES }
function callLine () {
  const match = new Error().stack.match(/PrivateKey\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('PrivateKey 入口缺少固定原测试调用位置')
  return Number(match[1])
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('PrivateKey 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function observe (method, args, action, describe) {
  if (depth !== 0 || !recording()) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? null : describe(result))
    return result
  } finally {
    depth--
  }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function string (value) { return { kind: 'string', value: String(value) } }
function encoding (value) { return value === undefined || value === null ? { kind: 'undefined' } : string(value) }
function privateKey (value) { return { kind: 'privateKey', hex: Reflect.apply(toHexOriginal, value, []) } }
function publicKey (value) { return { kind: 'publicKey', hex: value.toString() } }

// 原测试的随机私钥来自既有固定熵记录：两侧必须逐次同键，断言才能逐值比较。
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
      if (entropyActive()) record('random', [], { kind: 'entropy', length: array.length, bytesHex: hex(next) })
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
  iterations = 0
  if (!entropyCache.has(sourceFile)) entropyCache.set(sourceFile, loadEntropy(sourceFile))
  queue = (entropyCache.get(sourceFile).get(test) || []).slice()
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  const Original = moduleObject.default
  toHexOriginal = Original.prototype.toHex
  const originals = {
    fromString: Original.fromString,
    fromHex: Original.fromHex,
    fromRandom: Original.fromRandom,
    deriveChild: Original.prototype.deriveChild,
    toHex: Original.prototype.toHex,
    toString: Original.prototype.toString
  }
  Original.fromString = function (...args) {
    return observe('fromString', [string(args[0]), encoding(args[1])],
      () => Reflect.apply(originals.fromString, this, args), privateKey)
  }
  Original.fromHex = function (...args) {
    return observe('fromHex', [string(args[0])],
      () => Reflect.apply(originals.fromHex, this, args), privateKey)
  }
  Original.fromRandom = function (...args) {
    if (current() !== LOOP_TEST) {
      return observe('fromRandom', [], () => Reflect.apply(originals.fromRandom, this, args), privateKey)
    }
    const index = iterations++
    if (index >= LOOP_SAMPLES) return Reflect.apply(originals.fromRandom, this, args)
    return observe('fromRandom', [], () => Reflect.apply(originals.fromRandom, this, args), privateKey)
  }
  Original.prototype.toHex = function (...args) {
    return observe('toHex', [], () => Reflect.apply(originals.toHex, this, args), string)
  }
  Original.prototype.toString = function (...args) {
    return observe('toString', [encoding(args[0])],
      () => Reflect.apply(originals.toString, this, args), string)
  }
  Original.prototype.deriveChild = function (...args) {
    return observe('deriveChild', [publicKey(args[0]), string(args[1])],
      () => Reflect.apply(originals.deriveChild, this, args), privateKey)
  }
  return moduleObject
})
