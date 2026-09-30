// 固定 build.test.ts 的 20 条随机公钥构建用例：逐例确定性熵流，以及
// PrivateKey.fromRandom／PublicKey.fromString 两个公开入口的真实结果。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_AUTH_BUILD_TS_OBSERVATIONS
if (!output) throw new Error('缺少 build 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = testPath.slice(0, testPath.indexOf('/src/'))
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const callSite = new RegExp(sourceFile.split('/').pop().replace('.', '\\.') + ':(\\d+):\\d+')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let randomState = 0x243f6a88

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(callSite)
  return match ? Number(match[1]) : 0
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('build 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  randomState = 0x243f6a88
})

// Rand 经 globalThis.crypto.getRandomValues 取熵：替换为固定 xorshift 流并逐次记录。
const originalCrypto = globalThis.crypto
const entropy = { subtle: originalCrypto && originalCrypto.subtle }
Object.defineProperty(entropy, 'getRandomValues', { value (array) {
  for (let index = 0; index < array.length; index++) {
    randomState ^= randomState << 13
    randomState ^= randomState >>> 17
    randomState ^= randomState << 5
    array[index] = randomState >>> 24
  }
  if (current()) record('random', [], { kind: 'entropy', length: array.length,
    bytesHex: Buffer.from(array).toString('hex') })
  return array
} })
Object.defineProperty(globalThis, 'crypto', { configurable: true, value: entropy })

// 原测试经 mod.ts 取 PrivateKey／PublicKey；在 mod.ts 的模块工厂里加载真实模块并替换两个
// 静态入口，避开 mod.ts 内部循环导入导致的半初始化导出（静态导入在测试调用前已完成）。
const modPath = path.resolve(sdk, 'mod.ts')
jest.doMock(modPath, () => {
  const actual = jest.requireActual(modPath)
  const PrivateKeyClass = actual.PrivateKey
  const PublicKeyClass = actual.PublicKey
  if (typeof PrivateKeyClass?.fromRandom !== 'function' || typeof PublicKeyClass?.fromString !== 'function') {
    throw new Error('build 原输入采集：固定原语入口身份变化')
  }
  const originalFromRandom = PrivateKeyClass.fromRandom
  PrivateKeyClass.fromRandom = function (...args) {
    const line = callLine()
    const generated = Reflect.apply(originalFromRandom, this, args)
    record('fromRandom', [], { kind: 'return', value: generated.toPublicKey().toString() }, line)
    return generated
  }
  const originalFromString = PublicKeyClass.fromString
  PublicKeyClass.fromString = function (value, ...rest) {
    const line = callLine()
    const result = Reflect.apply(originalFromString, this, [value, ...rest])
    record('fromString', [value], { kind: 'return', value: result.toString() }, line)
    return result
  }
  return actual
})
