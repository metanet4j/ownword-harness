// 观察固定 utils.test.ts 的参数化 base58 用例；不修改测试和 SDK 实现。
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_BYTE_UTILS_OBSERVATIONS
if (!output) throw new Error('缺少 MIGRATION_BYTE_UTILS_OBSERVATIONS')
const nativeExpect = global.expect
const testPath = nativeExpect.getState().testPath
if (!testPath.endsWith('/src/primitives/__tests/utils.test.ts')) throw new Error('测试文件不匹配')
const sdk = path.resolve(path.dirname(testPath), '../../..')
const observed = []
const occurrences = new Map()
const selected = () => {
  const name = nativeExpect.getState().currentTestName || ''
  return name.endsWith('round-trips boundary byte values') ||
    name.endsWith('Converts to base58 as expected') ||
    name.endsWith('Converts to base58 as expected with 1s')
}

function value(input) {
  if (input === undefined) return { type: 'undefined' }
  if (input === null) return { type: 'null' }
  if (typeof input === 'string') return { type: 'string', value: input }
  if (typeof input === 'number') {
    const bits = Buffer.alloc(8)
    bits.writeDoubleBE(input)
    return { type: 'number', bits: bits.toString('hex') }
  }
  if (Array.isArray(input)) return { type: 'array', value: input.map(value) }
  throw new Error('未支持的 byte utils 输入类型：' + typeof input)
}

beforeEach(() => {
  if (!selected()) return
  // 等原测试静态导入完成，沿用其模块缓存，避免 setup 文件先触发另一套 TS 转换。
  const utils = require(path.join(sdk, 'src/primitives/utils.ts'))
  for (const method of ['toBase58', 'fromBase58']) {
    const original = utils[method]
    jest.spyOn(utils, method).mockImplementation(function (...args) {
      const call = { method, args: args.map(value) }
      try {
        const result = Reflect.apply(original, this, args)
        call.outcome = { kind: 'return', value: value(result) }
        return result
      } catch (error) {
        call.outcome = { kind: 'throw', name: error.name, message: error.message }
        throw error
      } finally {
        observed.push(call)
      }
    })
  }
})
afterEach(() => {
  jest.restoreAllMocks()
  if (observed.length) throw new Error('API 调用未对应原断言')
})

global.expect = Object.assign(function (actual) {
  if (!selected()) return nativeExpect(actual)
  const frame = new Error().stack.match(/\/utils\.test\.ts:(\d+):\d+/)
  if (!frame || ![128, 134, 142].includes(Number(frame[1]))) throw new Error('原断言位置不匹配')
  const assertion = nativeExpect(actual)
  return new Proxy(assertion, { get(target, matcher) {
    if (matcher !== 'toEqual') throw new Error('未支持的原断言：' + String(matcher))
    return (...args) => {
      try { return Reflect.apply(target[matcher], target, args) }
      finally {
        const test = nativeExpect.getState().currentTestName
        const occurrence = (occurrences.get(test) || 0) + 1
        occurrences.set(test, occurrence)
        fs.appendFileSync(output, JSON.stringify({ test, line: Number(frame[1]), occurrence,
          calls: observed.splice(0), matcher, actual: value(actual) }) + '\n')
      }
    }
  } })
}, nativeExpect)
