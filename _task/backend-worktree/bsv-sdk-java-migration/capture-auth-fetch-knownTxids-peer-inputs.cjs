// 观察固定 knownTxids 真实 Peer 付款原例的随机源、发送和回调输入。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.knownTxids.test.ts')
const caseId = '189790cbac0f42250b37519c090b906ad9619403b2b3dd8f02ee0be3fe1e1b09'
const selected = file.cases.find(item => item.id === caseId)
if (!selected) throw new Error('固定 knownTxids Peer 原例缺失')
const testName = selected.names.join(' ')
const undefinedValue = { type: 'undefined' }
function snapshot(value) {
  if (value === undefined) return undefinedValue
  if (Array.isArray(value)) return value.map(snapshot)
  if (value && typeof value === 'object') return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [key, snapshot(item)]))
  return value
}
async function resultOf(result) {
  if (result.type === 'throw') return { type: 'rejected', value: String(result.value) }
  try { await result.value; return { type: 'resolved', value: undefinedValue } }
  catch (error) { return { type: 'rejected', value: String(error) } }
}
let capture
const randomPath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/primitives/Random.ts')
jest.doMock(randomPath, () => {
  const actual = jest.requireActual(randomPath)
  const random = typeof actual === 'function' ? actual : actual.default
  return { __esModule: true, default: length => {
    const bytes = random(length)
    if (expect.getState().currentTestName === testName && capture)
      capture.requestNonces.push(snapshot(bytes))
    return bytes
  } }
})
// 与入口探针并用：本探针只补 Peer 观测；入口探针负责模块工厂，二者通过原型补丁组合。
const authPath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(authPath, () => {
  const actual = jest.requireActual(authPath)
  const original = actual.AuthFetch.prototype.fetch
  actual.AuthFetch.prototype.fetch = function (...args) {
    if (expect.getState().currentTestName !== testName) return Reflect.apply(original, this, args)
    if (!capture) {
        const origin = new URL(args[0]).origin
        const state = this.peers[origin]
        if (!state?.peer) throw new Error('固定 Peer 前置状态缺失')
        const peer = state.peer
        capture = { peer, peerState: {
            origin, identityKey: snapshot(state.identityKey),
            supportsMutualAuth: snapshot(state.supportsMutualAuth),
            pendingCertificateRequests: snapshot(state.pendingCertificateRequests),
            hasStopListeningForGeneralMessages: typeof peer.stopListeningForGeneralMessages === 'function'
        }, requestNonces: [], fetchCalls: [], delivered: [], listenerIds: [], starts: {
            listen: peer.listenForGeneralMessages.mock.calls.length,
            send: peer.toPeer.mock.calls.length,
            stop: peer.stopListeningForGeneralMessages.mock.calls.length
        } }
        const listen = peer.listenForGeneralMessages
        const implementation = listen.getMockImplementation()
        listen.mockImplementation(callback => {
            const id = implementation?.((sender, payload) => {
                capture.delivered.push({ sender, payload: snapshot(payload) })
                return callback(sender, payload)
            })
            capture.listenerIds.push(snapshot(id))
            return id
        })
        capture.restoreListen = () => listen.mockImplementation(implementation)
    }
    capture.fetchCalls.push({ url: args[0], config: args.length < 2 ? undefinedValue : snapshot(args[1]) })
    return Reflect.apply(original, this, args)
  }
  return actual
})

afterEach(async () => {
  if (expect.getState().currentTestName !== testName) return
  if (!capture) throw new Error('固定 knownTxids Peer 原例缺少入口观察')
  capture.restoreListen()
  const { peer, starts } = capture
  const sent = peer.toPeer.mock.calls.slice(starts.send)
    .map(args => ({ payload: snapshot(args[0]), identityKey: snapshot(args[1]) }))
  const sendResults = await Promise.all(peer.toPeer.mock.results.slice(starts.send).map(resultOf))
  const stoppedIds = peer.stopListeningForGeneralMessages.mock.calls.slice(starts.stop)
    .map(args => snapshot(args[0]))
  const listenCallCount = peer.listenForGeneralMessages.mock.calls.length - starts.listen
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId: 'call-0', value: {
    kind: 'AuthFetch.knownTxidsPeerInput', peerState: capture.peerState,
    requestNonces: capture.requestNonces, fetchCalls: capture.fetchCalls,
    listenerIds: capture.listenerIds, delivered: capture.delivered,
    sent, sendResults, stoppedIds, listenCallCount
  } }) + '\n')
  capture = undefined
})
