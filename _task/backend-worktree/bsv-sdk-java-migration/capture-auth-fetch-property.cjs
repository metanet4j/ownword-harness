// 在固定原测试调用 fast-check predicate 前记录真实生成值及后续 shrink 候选。
const fs = require('node:fs')
const actual = jest.requireActual('fast-check')
const fastCheck = actual.default
const output = process.env.MIGRATION_AUTH_FETCH_PROPERTY_TS_INPUTS
const metadata = process.env.MIGRATION_AUTH_FETCH_PROPERTY_TS_META
if (!output || !metadata) throw new Error('缺少 AuthFetch property 采集路径')
let configuration = null
let calls = 0
let firstFailure = null

const wrapped = new Proxy(fastCheck, {
  get(target, property) {
    if (property === 'configureGlobal') return config => {
      configuration = { ...config }
      return target.configureGlobal(config)
    }
    if (property === 'asyncProperty') return (...arguments_) => {
      const predicate = arguments_.pop()
      return target.asyncProperty(...arguments_, async (...values) => {
        const [status, declaredBodyLength, remoteBody] = values
        if (!Number.isInteger(status) || !Number.isInteger(declaredBodyLength) || !(remoteBody instanceof Uint8Array))
          throw new Error('固定 property 生成器参数类型变化')
        const index = ++calls
        fs.appendFileSync(output, JSON.stringify({ index, phase: firstFailure === null ? 'generate' : 'shrink',
          status, declaredBodyLength, remoteBody: Array.from(remoteBody) }) + '\n')
        try { return await predicate(...values) }
        catch (error) { if (firstFailure === null) firstFailure = index; throw error }
      })
    }
    if (property === 'assert') return (...arguments_) => {
      const result = target.assert(...arguments_)
      return Promise.resolve(result).then(
        value => { finish('passed'); return value },
        error => { finish('failed', error); throw error }
      )
    }
    return Reflect.get(target, property)
  }
})

function finish(status, error) {
  fs.writeFileSync(metadata, JSON.stringify({ status, configuration, fastCheckVersion: fastCheck.__version,
    calls, firstFailure,
    shrinkCalls: firstFailure === null ? 0 : calls - firstFailure,
    failure: error ? String(error.message) : null }, null, 2) + '\n')
}

jest.doMock('fast-check', () => ({ ...actual, __esModule: true, default: wrapped }))
