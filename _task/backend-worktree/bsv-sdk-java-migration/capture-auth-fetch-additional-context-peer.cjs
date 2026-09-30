// 固定 AuthFetch.additional 支付上下文与证书请求三个原用例的真实调用状态。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-additional-context-peer-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.additional.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 3) throw new Error('固定上下文/证书请求用例身份变化')

function record(caseId, method, input) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId: 'call-0',
    value: { kind: 'AuthFetch.contextPeerInput', method, input } }) + '\n')
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Fetch = actual.AuthFetch
  const payment = Fetch.prototype.handlePaymentAndRetry
  const certificate = Fetch.prototype.sendCertificateRequest
  Fetch.prototype.handlePaymentAndRetry = function (url, config, response) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (!caseId) return Reflect.apply(payment, this, [url, config, response])
    const configAtCall = JSON.parse(JSON.stringify(config))
    const status = response.status
    const statusText = response.statusText
    const headers = Object.fromEntries(response.headers.entries())
    const bodyUsed = response.bodyUsed
    const body = response.clone().text()
    const result = Reflect.apply(payment, this, [url, config, response])
    return Promise.resolve(result).finally(async () => record(caseId, 'handlePaymentAndRetry', {
      url, config: configAtCall,
      response: { status, statusText, headers, bodyUsed, bodyText: await body }
    }))
  }
  Fetch.prototype.sendCertificateRequest = function (url, requested) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (caseId) {
      const baseUrl = new URL(url).origin
      const state = this.peers[baseUrl]
      record(caseId, 'sendCertificateRequest', { url, requested,
        baseUrl, peerPresent: state !== undefined,
        pendingCertificateRequests: state?.pendingCertificateRequests === undefined
          ? null : [...state.pendingCertificateRequests] })
    }
    return Reflect.apply(certificate, this, [url, requested])
  }
  return actual
})
