// 观察固定 Peer 生命周期原测试的每次 fetch 入口、前置 Peer 状态与真实发送。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-peer-input-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.peer.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 6) throw new Error('固定 Peer 原用例身份变化')

const undefinedValue = { type: 'undefined' }
function snapshot(value) {
  if (value === undefined) return undefinedValue
  if (Array.isArray(value)) return value.map(snapshot)
  if (value && typeof value === 'object') return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [key, snapshot(item)]))
  return value
}
const observed = new Map()
const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const original = actual.AuthFetch.prototype.fetch
  actual.AuthFetch.prototype.fetch = function (...args) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (caseId) {
      if (!observed.has(caseId)) observed.set(caseId, { calls: [], client: this, peers: new Map() })
      const entry = observed.get(caseId)
      const origin = new URL(args[0]).origin
      const state = this.peers[origin]
      if (state?.peer) entry.peers.set(origin, state.peer)
      entry.calls.push({ url: args[0], config: args.length < 2 ? undefinedValue : snapshot(args[1]),
        origin, peerState: state === undefined ? undefinedValue : {
          identityKey: snapshot(state.identityKey), supportsMutualAuth: snapshot(state.supportsMutualAuth),
          pendingCertificateRequests: snapshot(state.pendingCertificateRequests),
          hasStopListeningForGeneralMessages: typeof state.peer.stopListeningForGeneralMessages === 'function'
        },
        constructorState: { requestedCertificates: snapshot(this.requestedCertificates),
          originator: snapshot(this.originator), walletHasGetPublicKey: typeof this.wallet?.getPublicKey === 'function' } })
    }
    return Reflect.apply(original, this, args)
  }
  return actual
})

afterEach(() => {
  const caseId = cases.get(expect.getState().currentTestName)
  if (!caseId) return
  const entry = observed.get(caseId)
  if (!entry || entry.calls.length === 0) throw new Error('固定 Peer 用例缺少真实 fetch 入口')
  const client = entry.client
  const origins = [...new Set(entry.calls.map(call => call.origin))]
  const peerCalls = origins.map(origin => {
    const peer = entry.peers.get(origin) ?? client.peers[origin]?.peer
    return { origin, sent: (peer?.toPeer?.mock?.calls ?? []).map(args =>
      ({ payload: snapshot(args[0]), identityKey: snapshot(args[1]) })),
      listenerIds: (peer?.listenForGeneralMessages?.mock?.results ?? []).map(result =>
        result.type === 'return' ? snapshot(result.value) : { type: 'throw' }),
      stoppedIds: (peer?.stopListeningForGeneralMessages?.mock?.calls ?? []).map(args => snapshot(args[0])) }
  })
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId: 'call-0',
    value: { kind: 'AuthFetch.peerInput', calls: entry.calls, peerCalls } }) + '\n')
  observed.delete(caseId)
})
