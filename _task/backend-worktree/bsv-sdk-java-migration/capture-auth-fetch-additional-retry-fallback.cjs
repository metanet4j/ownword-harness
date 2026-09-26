// 记录固定 AuthFetch.additional 四个 fetch 分支的真实调用和 mock 返回。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-additional-retry-fallback-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.additional.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 4) throw new Error('固定 retry/fallback 原用例身份变化')

function peerState(client, url) {
  const state = client.peers[new URL(url).origin]
  if (state === undefined) return { present: false }
  const peer = { present: true, supportsMutualAuth: state.supportsMutualAuth,
    pendingCertificateRequests: [...state.pendingCertificateRequests] }
  if (typeof state.identityKey === 'string') peer.identityKey = state.identityKey
  return peer
}

function fetchCall(client, url, config) {
  return { url, config: JSON.parse(JSON.stringify(config ?? {})), peer: peerState(client, url) }
}

function record(caseId, sampleId, value) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId,
    value: { kind: 'AuthFetch.retryFallbackInput', ...value } }) + '\n')
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const original = actual.AuthFetch.prototype.fetch
  const wrapper = function (url, config) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (!caseId) return Reflect.apply(original, this, [url, config])
    const name = file.cases.find(item => item.id === caseId).names.at(-1)
    const call = fetchCall(this, url, config)
    if (name === 'decrements retryCounter before making the request') {
      record(caseId, 'call-0', { fetch: call })
      const spy = this.fetch
      if (spy !== wrapper) {
        this.fetch = (...arguments_) => {
          record(caseId, 'call-1', { fetch: fetchCall(this, ...arguments_) })
          return Reflect.apply(spy, this, arguments_)
        }
      }
      return Reflect.apply(original, this, [url, config])
    }
    if (!name.startsWith('falls back') && !name.startsWith('rejects when handleFetchAndValidate')) {
      record(caseId, 'call-0', { fetch: call })
      return Reflect.apply(original, this, [url, config])
    }
    const mocked = this.handleFetchAndValidate
    let fallback
    this.handleFetchAndValidate = async (...arguments_) => {
      const [fallbackUrl, fallbackConfig, peer] = arguments_
      fallback = { url: fallbackUrl, config: JSON.parse(JSON.stringify(fallbackConfig)),
        peer: { supportsMutualAuth: peer.supportsMutualAuth } }
      try {
        const response = await Reflect.apply(mocked, this, arguments_)
        fallback.response = { status: response.status, statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries()), bodyUsed: response.bodyUsed,
          bodyText: await response.clone().text() }
        return response
      } catch (error) {
        fallback.error = { name: error.name, message: error.message }
        throw error
      }
    }
    return Promise.resolve(Reflect.apply(original, this, [url, config]))
      .finally(() => {
        if (!fallback) throw new Error('原 fallback mock 未被调用')
        record(caseId, 'call-0', { fetch: call, fallback })
      })
  }
  actual.AuthFetch.prototype.fetch = wrapper
  return actual
})
