// 固定 Broadcaster 原测试：记录两个守卫的实参及纯接口用例的实际属性读取。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_BROADCASTER_TS_OBSERVATIONS
const parity = process.env.MIGRATION_PARITY_TS_OBSERVATIONS
if (!output || !parity) throw new Error('缺少 Broadcaster 输入或断言采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/Broadcaster.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

const shapeCases = {
  'BroadcastResponse interface shape accepts competingTxs as an optional field': [
    ['competingTxs.length', 128, 'toHaveLength'], ['competingTxs', 135, 'toBeUndefined']
  ],
  'BroadcastFailure interface shape accepts txid and more as optional fields': [
    ['txid', 148, 'toBe'], ['more', 149, 'toEqual'],
    ['txid', 156, 'toBeUndefined'], ['more', 157, 'toBeUndefined']
  ]
}

beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function write (method, args, result, line) {
  const test = expect.getState().currentTestName
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    method, args, result, source: { file: sourceFile, line } }) + '\n')
}

function observeGuard (method, actual, result) {
  const line = new Error().stack.match(/Broadcaster\.test\.ts:(\d+):\d+/)
  if (!line) throw new Error('Broadcaster 原测试守卫入口缺少源码位置')
  write(method, [JSON.parse(JSON.stringify(actual))], result, Number(line[1]))
}

// 全量运行时 MIGRATION_PARITY_TS_OBSERVATIONS 是所有文件共享的断言轨迹，可能达数百 MB
// （个别用例会把大数组逐元素写进去），readFileSync(..., 'utf8') 会撞上 V8 的字符串上限。
// 因此按块扫描、只解析属于本用例的行，内存占用与文件大小无关。
function rowsForTest (file, test, occurrence) {
  const fd = fs.openSync(file, 'r')
  const size = fs.fstatSync(fd).size
  const chunk = 8 * 1024 * 1024
  const buffer = Buffer.allocUnsafe(chunk)
  const needle = '"' + test + '"'
  const rows = []
  let carry = ''
  const consider = text => {
    if (!text.includes(needle)) return
    const row = JSON.parse(text)
    if (row.test === test && row.occurrence === occurrence) rows.push(row)
  }
  for (let position = 0; position < size;) {
    const read = fs.readSync(fd, buffer, 0, chunk, position)
    position += read
    const text = carry + buffer.toString('utf8', 0, read)
    const lines = text.split('\n')
    carry = lines.pop()
    for (const line of lines) consider(line)
  }
  consider(carry)
  fs.closeSync(fd)
  return rows
}

afterEach(() => {
  const test = expect.getState().currentTestName
  const spec = shapeCases[test]
  if (!spec) return
  const rows = rowsForTest(parity, test, occurrence)
  if (rows.length !== spec.length || sequence !== 0) throw new Error('纯接口原用例属性读取数不同')
  const matcherCounts = new Map()
  rows.forEach((row, index) => {
    const [field, line, matcher] = spec[index]
    const count = (matcherCounts.get(matcher) || 0) + 1
    matcherCounts.set(matcher, count)
    if (row.matcher !== matcher || row.index !== count || row.pass !== true)
      throw new Error('纯接口原用例属性读取与固定原断言不一致')
    write('interfaceProperty', [{ field, actual: row.actual }], null, line)
  })
})

jest.doMock(modulePath, () => {
  const original = jest.requireActual(modulePath)
  return { ...original,
    isBroadcastResponse: function (actual) {
      const result = original.isBroadcastResponse(actual)
      observeGuard('isBroadcastResponse', actual, result)
      return result
    },
    isBroadcastFailure: function (actual) {
      const result = original.isBroadcastFailure(actual)
      observeGuard('isBroadcastFailure', actual, result)
      return result
    }, __esModule: true }
})
