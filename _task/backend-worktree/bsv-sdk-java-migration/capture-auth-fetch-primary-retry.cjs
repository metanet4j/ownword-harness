// 固定 AuthFetch 原测试两种付款重试的入口与真实 fetch/wait mock 返回。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-primary-retry-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 2) throw new Error('固定付款重试原用例身份变化')

function record(caseId, value) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId: 'call-0', value }) + '\n')
}

function mockReturns(mock, start) {
  if (!mock || !jest.isMockFunction(mock)) return []
  return Promise.all(mock.mock.results.slice(start).map(async result => {
    if (result.type === 'throw') return { type: 'rejected', name: result.value.name, message: result.value.message }
    try {
      const value = await result.value
      return { type: 'resolved', value: value === undefined ? { type: 'undefined' }
        : JSON.parse(JSON.stringify(value)) }
    } catch (error) {
      return { type: 'rejected', name: error.name, message: error.message }
    }
  }))
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
const active = new WeakSet()
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const original = actual.AuthFetch.prototype.handlePaymentAndRetry
  actual.AuthFetch.prototype.handlePaymentAndRetry = function (...args) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (!caseId) return Reflect.apply(original, this, args)
    if (active.has(this)) return Reflect.apply(original, this, args)
    active.add(this)
    const [url, config, response] = args
    const input = { url, config: JSON.parse(JSON.stringify(config)), response: {
      status: response.status, statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries()), bodyUsed: response.bodyUsed
    } }
    const body = response.clone().text()
    const fetchStart = this.fetch.mock.calls.length
    const waitStart = this.wait?.mock?.calls.length ?? 0
    const finish = async () => {
      input.response.bodyText = await body
      record(caseId, { kind: 'AuthFetch.primaryRetryInput', input,
        mockReturns: { fetch: await mockReturns(this.fetch, fetchStart),
          wait: await mockReturns(this.wait, waitStart) } })
    }
    return Promise.resolve(Reflect.apply(original, this, args)).then(
      async value => { await finish(); return value },
      async error => { await finish(); throw error }
    ).finally(() => active.delete(this))
  }
  return actual
})
