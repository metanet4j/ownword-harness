// 固定原测试在 handleFetchAndValidate 消费前捕获参数、缺省状态和 mocked Response。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-additional-validated-fallback-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.additional.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 3) throw new Error('固定 validated fallback 用例身份变化')

function state(value) {
  if (value === undefined) return { type: 'undefined' }
  if (value === null) return { type: 'null' }
  return { type: typeof value, value }
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const original = actual.AuthFetch.prototype.handleFetchAndValidate
  actual.AuthFetch.prototype.handleFetchAndValidate = function (url, config, peer) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (!caseId) return Reflect.apply(original, this, [url, config, peer])
    const peerAtCall = state(peer.supportsMutualAuth)
    const originalFetch = global.fetch
    let response
    global.fetch = (...arguments_) => Promise.resolve(Reflect.apply(originalFetch, global, arguments_))
      .then(value => { response = value; return value })
    return Promise.resolve(Reflect.apply(original, this, [url, config, peer]))
      .finally(async () => {
        global.fetch = originalFetch
        if (!response) throw new Error('固定 global.fetch mock 没有被调用')
        const value = { kind: 'AuthFetch.validatedFallbackInput', url,
          config: JSON.parse(JSON.stringify(config)),
          peer: { supportsMutualAuth: peerAtCall },
          response: { status: response.status, statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries()), bodyUsed: response.bodyUsed,
            bodyText: await response.clone().text() } }
        fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId,
          sampleId: 'call-0', value }) + '\n')
      })
  }
  return actual
})
