// 在固定原测试的 fast-check predicate 边界记录实际生成及 shrink 输入。
const fs = require('node:fs')
const path = require('node:path')
const actual = jest.requireActual('fast-check')
const fastCheck = actual.default
const output = process.env.MIGRATION_UTILS_PROPERTY_TS_INPUTS
const metadata = process.env.MIGRATION_UTILS_PROPERTY_TS_META
const boundaries = process.env.MIGRATION_UTILS_PROPERTY_TS_BOUNDARIES
if (!output || !metadata || !boundaries) throw new Error('缺少 utils property 采集路径')

let configuration
const runs = []
let active
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
        if (!test || !values.every(value => value instanceof Uint8Array))
          throw new Error('固定 utils property 生成器或测试名称变化')
        const index = active.calls + 1
        fs.appendFileSync(output, JSON.stringify({ test, index,
          phase: active.firstFailure === null ? 'generate' : 'shrink',
          inputs: values.map(value => Array.from(value)) }) + '\n')
        active.calls++
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
        runs.push({ ...active, status: 'failed',
          shrinkCalls: active.calls - active.firstFailure, failure: String(error.message) })
        throw error
      } finally {
        fs.writeFileSync(metadata, JSON.stringify({ configuration, runs }, null, 2) + '\n')
      }
    }
    return Reflect.get(target, name)
  }
})

jest.doMock('fast-check', () => ({ ...actual, __esModule: true, default: wrapped }))

const parentExpect = global.expect
const calls = []
const boundaryTest = 'base58 property tests matches independent vectors and enforces malformed-input and hex-output boundaries'
const selected = () => parentExpect.getState().currentTestName === boundaryTest
beforeEach(() => {
  if (!selected()) return
  const testPath = parentExpect.getState().testPath
  if (!testPath.endsWith('/src/primitives/__tests/utils.property.test.ts'))
    throw new Error('固定原测试文件变化')
  const utils = require(path.resolve(path.dirname(testPath), '../utils.ts'))
  for (const method of ['fromBase58', 'toBase58', 'fromBase58Check', 'toBase58Check']) {
    const original = utils[method]
    jest.spyOn(utils, method).mockImplementation(function (...args) {
      const call = { method, args }
      try { return Reflect.apply(original, this, args) }
      finally { calls.push(call) }
    })
  }
})
afterEach(() => {
  jest.restoreAllMocks()
  if (calls.length) throw new Error('边界输入未对应原断言')
})

global.expect = Object.assign(function (received) {
  const assertion = parentExpect(received)
  if (!selected()) return assertion
  return new Proxy(assertion, { get(target, matcher) {
    if (!['toEqual', 'toBe', 'toThrow'].includes(String(matcher)))
      throw new Error('固定边界断言类型变化：' + String(matcher))
    return (...args) => {
      try { return Reflect.apply(target[matcher], target, args) }
      finally {
        fs.appendFileSync(boundaries, JSON.stringify({ matcher, calls: calls.splice(0).map(call => ({
          method: call.method, args: call.args.map(value =>
            value instanceof Uint8Array ? Array.from(value) : value)
        })) }) + '\n')
      }
    }
  } })
}, parentExpect)
