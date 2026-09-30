// 固定 AuthFetch.additional 七个错误构造原用例，记录调用前的真实参数。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-additional-errors-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.additional.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 7) throw new Error('固定错误构造用例身份变化')

function errorValue(value) {
  if (value instanceof Error) return { kind: 'Error', name: value.name,
    message: value.message, stack: value.stack }
  return { kind: typeof value, value }
}

function record(caseId, method, input) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId: 'call-0',
    value: { kind: 'AuthFetch.errorInput', method, input } }) + '\n')
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Fetch = actual.AuthFetch
  const entry = Fetch.prototype.createPaymentErrorEntry
  const failure = Fetch.prototype.buildPaymentFailureError
  Fetch.prototype.createPaymentErrorEntry = function (attempt, error) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (caseId) record(caseId, 'createPaymentErrorEntry', { attempt, error: errorValue(error) })
    return Reflect.apply(entry, this, [attempt, error])
  }
  Fetch.prototype.buildPaymentFailureError = function (url, context, lastError) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (caseId) record(caseId, 'buildPaymentFailureError',
      { url, context, lastError: errorValue(lastError) })
    return Reflect.apply(failure, this, [url, context, lastError])
  }
  return actual
})
