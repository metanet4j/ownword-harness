// 固定 DefaultChainTracker 原测试：采集工厂与追踪器方法的真实调用。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_DEFAULT_CHAIN_TRACKER_TS_OBSERVATIONS
if (!output) throw new Error('缺少 MIGRATION_DEFAULT_CHAIN_TRACKER_TS_OBSERVATIONS')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.resolve(path.dirname(testPath), '../DefaultChainTracker.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let instanceOrdinal = 0

beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  instanceOrdinal = 0
})

function observe (method, args, result) {
  const test = expect.getState().currentTestName
  if (!test) return
  const line = new Error().stack.match(/DefaultChainTracker\.test\.ts:(\d+):\d+/)
  if (!line) throw new Error('DefaultChainTracker 原测试入口缺少源码位置')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    method, args, result, source: { file: sourceFile, line: Number(line[1]) } }) + '\n')
}

jest.doMock(modulePath, () => {
  const original = jest.requireActual(modulePath)
  return { ...original, defaultChainTracker: function (...args) {
    const tracker = original.defaultChainTracker(...args)
    observe('defaultChainTracker', args, {
      className: tracker.constructor.name,
      network: tracker.network,
      methodType: typeof tracker.isValidRootForHeight,
      instanceOrdinal: ++instanceOrdinal
    })
    let methodReads = 0
    return new Proxy(tracker, { get (target, key, receiver) {
      if (key !== 'isValidRootForHeight') return Reflect.get(target, key, receiver)
      if (++methodReads === 1) return Reflect.get(target, key, receiver)
      return function (...methodArgs) {
        const result = target.isValidRootForHeight(...methodArgs)
        observe('isValidRootForHeight', methodArgs,
          { kind: 'Promise', thenType: typeof result.then })
        return result
      }
    } })
  }, __esModule: true }
})
