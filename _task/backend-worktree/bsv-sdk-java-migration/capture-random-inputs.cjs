// 固定 Random.test.ts 的原输入：只记录原测试真实发起的随机入口。
// 随机入口按原语言的 getRandomValues 观察形状记录实际字节（kind: entropy），
// Java 侧用同一份字节重放，保证两侧可比部分一致。
// 断言由 capture-parity-array-length.cjs 采集（数组型 toHaveLength 记录原始字节数组）。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_RANDOM_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Random 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')

const occurrences = new Map()
let occurrence = 0
let sequence = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/Random\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('Random 入口缺少固定原测试调用位置')
  return Number(match[1])
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('Random 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

// 原测试的随机来自 Web Crypto；探针只观察并记录实际字节，不改动随机源。
const source = globalThis.crypto
const patched = Object.create(source)
Object.defineProperty(patched, 'getRandomValues', {
  value (array) {
    const result = Reflect.apply(source.getRandomValues, source, [array])
    record('random', [], { kind: 'entropy', length: result.length, bytesHex: hex(result) })
    return result
  }
})
Object.defineProperty(globalThis, 'crypto', { configurable: true, value: patched })
