// 在固定 BRC-100 fast-check predicate 边界记录每一轮真实输入及失败后的 shrink 候选。
const fs = require('node:fs')
const actual = jest.requireActual('fast-check')
const fastCheck = actual.default
const output = process.env.MIGRATION_WALLET_PROPERTY_TS_INPUTS
const metadata = process.env.MIGRATION_WALLET_PROPERTY_TS_META
if (!output || !metadata) throw new Error('缺少 wallet property 采集路径')

const TESTS = [
  'BRC-100 JSON compatibility properties preserves every ordinary JSON value exactly',
  'BRC-100 JSON compatibility properties serializes actual typed arrays portably without reinterpreting adjacent JSON'
]
let configuration
let active
const runs = []

function string(input) {
  return { type: 'string', units: Array.from({ length: input.length }, (_, index) => input.charCodeAt(index)) }
}

function tagged(input) {
  if (input === null) return { type: 'null' }
  if (typeof input === 'boolean') return { type: 'boolean', value: input }
  if (typeof input === 'number') {
    const bits = Buffer.alloc(8)
    bits.writeDoubleBE(input)
    return { type: 'number', bits: bits.toString('hex') }
  }
  if (typeof input === 'string') return string(input)
  if (input instanceof Uint8Array) return { type: 'uint8array', bytes: Array.from(input) }
  if (Array.isArray(input)) return { type: 'array', value: input.map(tagged) }
  if (typeof input === 'object' && Object.getPrototypeOf(input) === Object.prototype) {
    return { type: 'object', entries: Object.entries(input).map(([key, value]) => ({ key: string(key), value: tagged(value) })) }
  }
  throw new Error('固定 wallet property 出现未支持的生成类型：' + typeof input)
}

const wrapped = new Proxy(fastCheck, {
  get(target, name) {
    if (name === 'configureGlobal') return config => {
      configuration = { ...config }
      return target.configureGlobal(config)
    }
    if (name === 'property') return (...args) => {
      const predicate = args.pop()
      return target.property(...args, (...values) => {
        const test = expect.getState().currentTestName
        if (!active || test !== active.test || !TESTS.includes(test)
            || values.length !== (test === TESTS[0] ? 1 : 2)
            || (test === TESTS[1] && !(values[0] instanceof Uint8Array)))
          throw new Error('固定 wallet property 生成器或用例名称变化')
        const index = ++active.calls
        fs.appendFileSync(output, JSON.stringify({ test, index,
          phase: active.firstFailure === null ? 'generate' : 'shrink', inputs: values.map(tagged) }) + '\n')
        try { return predicate(...values) }
        catch (error) { if (active.firstFailure === null) active.firstFailure = index; throw error }
      })
    }
    if (name === 'assert') return (...args) => {
      active = { test: expect.getState().currentTestName, calls: 0, firstFailure: null }
      try {
        const result = target.assert(...args)
        runs.push({ ...active, status: 'passed', shrinkCalls: 0 })
        return result
      } catch (error) {
        runs.push({ ...active, status: 'failed', shrinkCalls: active.calls - active.firstFailure,
          failure: String(error.message) })
        throw error
      } finally {
        fs.writeFileSync(metadata, JSON.stringify({ configuration, fastCheckVersion: fastCheck.__version, runs }, null, 2) + '\n')
      }
    }
    return Reflect.get(target, name)
  }
})

jest.doMock('fast-check', () => ({ ...actual, __esModule: true, default: wrapped }))
