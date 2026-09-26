// 固定 AuthFetch.additional 八个支付响应头原用例，采集完整调用与 Response 前置状态。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-additional-payment-headers-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.additional.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 8) throw new Error('固定支付响应头用例身份变化')

function record(caseId, input) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId: 'call-0',
    value: { kind: 'AuthFetch.paymentHeaderInput', method: 'handlePaymentAndRetry', input } }) + '\n')
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Fetch = actual.AuthFetch
  const handle = Fetch.prototype.handlePaymentAndRetry
  Fetch.prototype.handlePaymentAndRetry = function (url, config, response) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (!caseId) return Reflect.apply(handle, this, [url, config, response])
    const body = response.clone().text()
    const status = response.status
    const statusText = response.statusText
    const headers = Object.fromEntries(response.headers.entries())
    const bodyUsed = response.bodyUsed
    const result = Reflect.apply(handle, this, [url, config, response])
    return Promise.resolve(result).finally(async () => record(caseId, {
      url, config, response: { status, statusText, headers, bodyUsed, bodyText: await body }
    }))
  }
  return actual
})
