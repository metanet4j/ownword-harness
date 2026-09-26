// 观察固定 AuthFetch 边界原测试的入口、Peer 前置状态和 mock 实际输入。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-boundary-input-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.boundary.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 15) throw new Error('固定边界原用例身份变化')

const undefinedValue = { type: 'undefined' }
function valueOf(value) {
  if (value === undefined) return undefinedValue
  if (value instanceof Error || (value && typeof value.name === 'string' && typeof value.message === 'string'))
    return { type: 'error', name: value.name, message: value.message,
    details: value.details === undefined ? undefinedValue : valueOf(value.details) }
  if (Array.isArray(value)) return value.map(valueOf)
  if (value && typeof value === 'object') return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [key, valueOf(item)]))
  return value
}
async function resultOf(result) {
  if (result.type === 'throw') return { type: 'rejected', value: valueOf(result.value) }
  try {
    const value = await result.value
    if (value instanceof Response) return { type: 'resolved', value: { status: value.status,
      headers: Object.fromEntries(value.headers.entries()), bodyText: await value.clone().text() } }
    return { type: 'resolved', value: valueOf(value) }
  } catch (error) {
    return { type: 'rejected', value: valueOf(error) }
  }
}

const captures = new Map()
const active = new WeakSet()
const randomPath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/primitives/Random.ts')
jest.doMock(randomPath, () => {
  const actual = jest.requireActual(randomPath)
  const random = typeof actual === 'function' ? actual : actual.default
  return { __esModule: true, default: len => {
    const bytes = random(len)
    const caseId = cases.get(expect.getState().currentTestName)
    const capture = captures.get(caseId)
    if (capture) capture.input.requestNonces.push(valueOf(bytes))
    return bytes
  } }
})
const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const original = actual.AuthFetch.prototype.fetch
  actual.AuthFetch.prototype.fetch = function (...args) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (!caseId || active.has(this)) return Reflect.apply(original, this, args)
    if (captures.has(caseId)) throw new Error('固定边界用例出现额外入口调用')
    active.add(this)
    const origin = new URL(args[0]).origin
    const state = this.peers[origin]
    if (!state?.peer) throw new Error('固定边界 Peer 前置状态变化')
    const peer = state.peer
    const input = {
      url: args[0],
      config: args.length < 2 ? undefinedValue : valueOf(args[1]),
      peerState: {
        origin,
        identityKey: valueOf(state.identityKey),
        supportsMutualAuth: valueOf(state.supportsMutualAuth),
        pendingCertificateRequests: valueOf(state.pendingCertificateRequests),
        hasStopListeningForGeneralMessages: typeof peer.stopListeningForGeneralMessages === 'function'
      },
      pendingRequestNonces: [...this.pendingRequestNonces],
      requestNonces: []
    }
    const observations = { listenerIds: [], delivered: [], sent: [], stoppedIds: [] }
    const capture = { input, observations, peer, starts: {
      listen: peer.listenForGeneralMessages?.mock?.calls.length ?? 0,
      send: peer.toPeer?.mock?.calls.length ?? 0,
      stop: peer.stopListeningForGeneralMessages?.mock?.calls.length ?? 0,
      wait: this.waitForPendingCertificateRequests?.mock?.calls.length ?? 0,
      fallback: this.handleFetchAndValidate?.mock?.calls.length ?? 0,
      fetch: this.fetch?.mock?.calls.length ?? 0
    } }
    capture.client = this
    captures.set(caseId, capture)
    const originalListen = peer.listenForGeneralMessages
    if (jest.isMockFunction(originalListen)) {
      const implementation = originalListen.getMockImplementation()
      originalListen.mockImplementation(callback => {
        const result = implementation?.((sender, payload) => {
          observations.delivered.push({ sender, payload: valueOf(payload) })
          return callback(sender, payload)
        })
        observations.listenerIds.push(valueOf(result))
        return result
      })
      capture.restoreListen = () => originalListen.mockImplementation(implementation)
    }
    const promise = Reflect.apply(original, this, args)
    return Promise.resolve(promise).finally(() => active.delete(this))
  }
  return actual
})

afterEach(async () => {
  const caseId = cases.get(expect.getState().currentTestName)
  if (!caseId) return
  const capture = captures.get(caseId)
  if (!capture) throw new Error('固定边界用例缺少真实入口观察')
  capture.restoreListen?.()
  const { peer, starts, observations, input } = capture
  observations.sent = (peer.toPeer?.mock?.calls ?? []).slice(starts.send)
    .map(args => ({ payload: valueOf(args[0]), identityKey: valueOf(args[1]) }))
  observations.sendResults = await Promise.all((peer.toPeer?.mock?.results ?? [])
    .slice(starts.send).map(resultOf))
  observations.waitResults = await Promise.all((capture.client.waitForPendingCertificateRequests?.mock?.results ?? [])
    .slice(starts.wait).map(resultOf))
  observations.fallbackResults = await Promise.all((capture.client.handleFetchAndValidate?.mock?.results ?? [])
    .slice(starts.fallback).map(resultOf))
  observations.fetchResults = await Promise.all((capture.client.fetch?.mock?.results ?? [])
    .slice(starts.fetch).map(resultOf))
  observations.stoppedIds = (peer.stopListeningForGeneralMessages?.mock?.calls ?? [])
    .slice(starts.stop).map(args => valueOf(args[0]))
  observations.listenCallCount = (peer.listenForGeneralMessages?.mock?.calls.length ?? 0) - starts.listen
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId: 'call-0',
    value: { kind: 'AuthFetch.boundaryInput', input, mockInputs: observations } }) + '\n')
  captures.delete(caseId)
})
