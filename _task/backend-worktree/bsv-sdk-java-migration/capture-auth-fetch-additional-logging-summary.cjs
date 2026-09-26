// 固定 AuthFetch.additional 六个日志与请求摘要原用例的真实参数及 console 前置状态。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-additional-logging-summary-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.additional.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 6) throw new Error('固定日志/摘要用例身份变化')

function record(caseId, method, input) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId: 'call-0',
    value: { kind: 'AuthFetch.loggingSummaryInput', method, input } }) + '\n')
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Fetch = actual.AuthFetch
  const log = Fetch.prototype.logPaymentAttempt
  const summary = Fetch.prototype.buildPaymentRequestSummary
  Fetch.prototype.logPaymentAttempt = function (level, message, details) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (caseId) record(caseId, 'logPaymentAttempt', { level, message, details,
      infoAvailable: typeof console.info === 'function' })
    return Reflect.apply(log, this, [level, message, details])
  }
  Fetch.prototype.buildPaymentRequestSummary = function (url, config) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (caseId) record(caseId, 'buildPaymentRequestSummary', { url, config })
    return Reflect.apply(summary, this, [url, config])
  }
  return actual
})
