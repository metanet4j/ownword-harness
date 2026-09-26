// 固定 toOriginHeader 原测试：采集直接调用的实参、结果或异常。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_ORIGIN_HEADER_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Origin 输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/wallet/substrates/utils/toOriginHeader.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(modulePath, () => {
  const original = jest.requireActual(modulePath)
  return { ...original, toOriginHeader (...args) {
    const match = new Error().stack.match(/toOriginHeader\.test\.ts:(\d+):\d+/)
    if (!match) throw new Error('Origin 原用例缺少直接调用位置')
    const event = { test: expect.getState().currentTestName, occurrence,
      sequence: ++sequence, source: { file: sourceFile, line: Number(match[1]) },
      method: 'toOriginHeader', args }
    try {
      const result = original.toOriginHeader(...args)
      event.result = { kind: 'return', value: result }
      fs.appendFileSync(output, JSON.stringify(event) + '\n')
      return result
    } catch (error) {
      event.result = { kind: 'throw', name: error.name, message: error.message }
      fs.appendFileSync(output, JSON.stringify(event) + '\n')
      throw error
    }
  } }
})
