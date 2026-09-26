// 固定 AuthFetch 原测试三种证书请求的入口与 Peer mock 交互。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-primary-cert-request-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 3) throw new Error('固定证书请求原用例身份变化')

function record(caseId, value) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId: 'call-0', value }) + '\n')
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const original = actual.AuthFetch.prototype.sendCertificateRequest
  actual.AuthFetch.prototype.sendCertificateRequest = function (url, requested) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (!caseId) return Reflect.apply(original, this, [url, requested])
    const origin = new URL(url).origin
    const state = this.peers[origin]
    if (!state?.peer) throw new Error('固定证书请求 Peer 前置状态变化')
    const peer = state.peer
    const input = { url, requested: JSON.parse(JSON.stringify(requested)),
      peerState: { origin, existing: true,
        pendingCertificateRequests: JSON.parse(JSON.stringify(state.pendingCertificateRequests)) } }
    const delivered = []
    const originalListen = peer.listenForCertificatesReceived
    peer.listenForCertificatesReceived = callback => originalListen((sender, certs) => {
      delivered.push({ sender, certificates: JSON.parse(JSON.stringify(certs)) })
      return callback(sender, certs)
    })
    const listenStart = originalListen.mock.results.length
    const requestStart = peer.requestCertificates.mock.results.length
    const stopStart = peer.stopListeningForCertificatesReceived.mock.calls.length
    const finish = async () => {
      const listen = originalListen.mock.results.slice(listenStart)
      const request = peer.requestCertificates.mock.results.slice(requestStart)
      if (listen.length !== 1 || request.length !== 1)
        throw new Error('固定证书请求 Peer mock 调用次数变化')
      const requestArgs = peer.requestCertificates.mock.calls[requestStart]
      input.requestIdentityKey = requestArgs.length < 2 || requestArgs[1] === undefined
        ? { type: 'undefined' } : requestArgs[1]
      let requestResult
      try {
        const value = await request[0].value
        requestResult = { type: 'resolved', value: value === undefined
          ? { type: 'undefined' } : JSON.parse(JSON.stringify(value)) }
      } catch (error) {
        requestResult = { type: 'rejected', name: error.name, message: error.message }
      }
      record(caseId, { kind: 'AuthFetch.primaryCertificateRequestInput', input,
        mockReturns: { listenId: listen[0].value, request: requestResult, delivered,
          stoppedIds: peer.stopListeningForCertificatesReceived.mock.calls.slice(stopStart)
            .map(args => args[0]) } })
    }
    return Promise.resolve(Reflect.apply(original, this, [url, requested])).then(
      async value => { await finish(); return value },
      async error => { await finish(); throw error }
    ).finally(() => { peer.listenForCertificatesReceived = originalListen })
  }
  return actual
})
