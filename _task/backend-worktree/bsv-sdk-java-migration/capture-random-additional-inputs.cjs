// 固定 Random.additional.test.ts 的原输入：只登记原测试真实发起的 Random(len) 入口。
// 结果按原语言实际观察形状记录：可用时是字节数组（kind: numberArray），
// 环境分支不可用时是异常（kind: throw）；Java 侧用同一份结果重放，
// 因此随机源与环境分支两侧完全同输入。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_RANDOM_ADDITIONAL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Random.additional 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/primitives/Random.ts')

const occurrences = new Map()
let occurrence = 0
let sequence = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/Random\.additional\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('Random.additional 入口缺少固定原测试调用位置')
  return Number(match[1])
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('Random.additional 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function observe (method, args, action) {
  try {
    const result = action()
    record(method, args, numberArray(result))
    return result
  } catch (error) {
    record(method, args, thrown(error))
    throw error
  }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function number (value) { return { kind: 'number', value: String(value) } }
function numberArray (value) {
  return { kind: 'numberArray', length: value.length, hex: hex(Uint8Array.from(value)) }
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw',
    name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

// 原测试每个环境变体都用 jest.isolateModules 重新加载模块，因此工厂每次都要返回包装后的入口。
jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (moduleObject.default === undefined) return moduleObject
  const Original = moduleObject.default
  const Random = function (len) {
    return observe('Random', [number(len)], () => Original(len))
  }
  return { ...moduleObject, __esModule: true, default: Random }
})
