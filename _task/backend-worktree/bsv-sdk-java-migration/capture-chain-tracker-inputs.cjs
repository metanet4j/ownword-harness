// 固定 ChainTracker 原测试：记录类型守卫实际接收的值与对象形状。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_CHAIN_TRACKER_TS_OBSERVATIONS
if (!output) throw new Error('缺少 MIGRATION_CHAIN_TRACKER_TS_OBSERVATIONS')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/ChainTracker.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function snapshot (value) {
  if (value === undefined) return { kind: 'Undefined' }
  if (value === null) return { kind: 'Null' }
  if (typeof value === 'string') return { kind: 'String', value }
  if (typeof value === 'number') return { kind: 'Number', value: String(value) }
  if (typeof value === 'object') {
    return { kind: 'Object', fields: Object.fromEntries(Object.keys(value).sort().map(key =>
      [key, typeof value[key]])) }
  }
  throw new Error('ChainTracker 守卫原参数类型尚未表征')
}

function observe (actual, result) {
  const test = expect.getState().currentTestName
  if (!test) return
  const line = new Error().stack.match(/ChainTracker\.test\.ts:(\d+):\d+/)
  if (!line) throw new Error('ChainTracker 原测试守卫调用缺少源码位置')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    method: 'isChainTracker', args: [snapshot(actual)], result,
    source: { file: sourceFile, line: Number(line[1]) } }) + '\n')
}

jest.doMock(modulePath, () => {
  const original = jest.requireActual(modulePath)
  return { ...original, isChainTracker: function (actual) {
    const result = original.isChainTracker(actual)
    observe(actual, result)
    return result
  }, __esModule: true }
})
