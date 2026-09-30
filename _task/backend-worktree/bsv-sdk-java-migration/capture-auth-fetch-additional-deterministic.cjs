// 固定 AuthFetch.additional 的 15 个确定性原用例：记录方法实际收到的参数与队列前置状态。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-additional-deterministic-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.additional.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 15) throw new Error('固定 AuthFetch 确定性用例身份变化')
const counts = new Map()

function plain(value) {
  if (Array.isArray(value)) return value.map(plain)
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value)
    .map(([key, item]) => [key, plain(item)]))
  return value
}

function record(caseId, method, input) {
  const index = counts.get(caseId) || 0
  counts.set(caseId, index + 1)
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId,
    sampleId: `call-${index}`, value: { kind: 'AuthFetch.deterministicInput', method, input } }) + '\n')
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Fetch = actual.AuthFetch
  const methods = {
    getMaxPaymentAttempts: (self, args) => ({ config: plain(args[0]) }),
    getPaymentRetryDelay: (self, args) => ({ attempt: args[0] }),
    isPaymentContextCompatible: (self, args) => ({ context: plain(args[0]),
      satoshisRequired: args[1], serverIdentityKey: args[2], derivationPrefix: args[3] }),
    consumeReceivedCertificates: self => ({ certificatesReceived: plain(self.certificatesReceived) })
  }
  for (const [name, snapshot] of Object.entries(methods)) {
    const original = Fetch.prototype[name]
    Fetch.prototype[name] = function (...args) {
      const caseId = cases.get(expect.getState().currentTestName)
      if (caseId) record(caseId, name, snapshot(this, args))
      return Reflect.apply(original, this, args)
    }
  }
  return actual
})
