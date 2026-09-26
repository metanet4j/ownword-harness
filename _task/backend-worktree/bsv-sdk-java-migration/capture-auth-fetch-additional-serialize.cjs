// 固定 AuthFetch.additional 的 10 个 serializeRequest 原用例：记录方法真实五参数。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-additional-serialize-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.additional.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 10) throw new Error('固定 serializeRequest 用例身份变化')

function bodyValue(body) {
  if (body === undefined) return { type: 'undefined' }
  if (body === null) return { type: 'null' }
  if (typeof body === 'string') return { type: 'string', value: body }
  return { type: 'object', value: body }
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Fetch = actual.AuthFetch
  const original = Fetch.prototype.serializeRequest
  Fetch.prototype.serializeRequest = function (method, headers, body, url, nonce) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (caseId) {
      fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId,
        sampleId: 'serialize-0', value: { kind: 'AuthFetch.serializeRequestInput',
          method, headers, body: bodyValue(body), url: url.toString(), nonce: Array.from(nonce) } }) + '\n')
    }
    return Reflect.apply(original, this, [method, headers, body, url, nonce])
  }
  return actual
})
