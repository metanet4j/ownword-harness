// 固定 AuthFetch.additional 五个等待用例，采集方法实参和时间源调用。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-additional-wait-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.additional.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 5) throw new Error('固定等待用例身份变化')

function record(caseId, method, input) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId: 'call-0',
    value: { kind: 'AuthFetch.waitInput', method, input } }) + '\n')
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Fetch = actual.AuthFetch
  const wait = Fetch.prototype.wait
  const pending = Fetch.prototype.waitForPendingCertificateRequests
  Fetch.prototype.wait = function (ms) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (caseId && plan[caseId].assertionIds.some(id => /:(822|829|840):/.test(id)))
      record(caseId, 'wait', { ms })
    return Reflect.apply(wait, this, [ms])
  }
  Fetch.prototype.waitForPendingCertificateRequests = function (peer) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (!caseId) return Reflect.apply(pending, this, [peer])
    const initialPending = [...peer.pendingCertificateRequests]
    const waitMocked = jest.isMockFunction(this.wait)
    const clock = Date.now
    const clockReads = []
    Date.now = function () {
      const value = Reflect.apply(clock, Date, [])
      clockReads.push(value)
      return value
    }
    let result
    try {
      result = Reflect.apply(pending, this, [peer])
    } catch (error) {
      Date.now = clock
      record(caseId, 'waitForPendingCertificateRequests',
        { pendingCertificateRequests: initialPending, waitMocked, clockReads })
      throw error
    }
    return Promise.resolve(result).finally(() => {
      Date.now = clock
      record(caseId, 'waitForPendingCertificateRequests',
        { pendingCertificateRequests: initialPending, waitMocked, clockReads })
    })
  }
  return actual
})
