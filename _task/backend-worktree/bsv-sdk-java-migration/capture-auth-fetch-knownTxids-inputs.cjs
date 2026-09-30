// 观察固定 knownTxids 原测试的所有解析调用与付款入口；同例多次调用保留顺序。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-knownTxids-input-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.knownTxids.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 17) throw new Error('固定 knownTxids 原用例身份变化')

const undefinedValue = { type: 'undefined' }
function snapshot(value) {
  if (value === undefined) return undefinedValue
  if (Array.isArray(value)) return value.map(snapshot)
  if (value && typeof value === 'object') return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [key, snapshot(item)]))
  return value
}
const observed = new Map()
function group() {
  const caseId = cases.get(expect.getState().currentTestName)
  if (!caseId) return null
  if (!observed.has(caseId)) observed.set(caseId, { parseCalls: [], paymentCalls: [] })
  return observed.get(caseId)
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const parse = actual.parseKnownTxidsHeader
  const payment = actual.AuthFetch.prototype.handlePaymentAndRetry
  actual.AuthFetch.prototype.handlePaymentAndRetry = function (...args) {
    const target = group()
    if (target) {
      const [url, config, response] = args
      const call = { url, config: snapshot(config), response: {
        status: response.status, statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        bodyUsed: response.bodyUsed
      } }
      target.paymentCalls.push(call)
      call.bodyText = response.clone().text()
    }
    return Reflect.apply(payment, this, args)
  }
  return { ...actual, parseKnownTxidsHeader: (...args) => {
    const target = group()
    if (target) target.parseCalls.push({ header: args.length === 0 ? undefinedValue : snapshot(args[0]) })
    return Reflect.apply(parse, null, args)
  } }
})

afterEach(async () => {
  const caseId = cases.get(expect.getState().currentTestName)
  if (!caseId) return
  const entry = observed.get(caseId)
  if (!entry || entry.parseCalls.length + entry.paymentCalls.length === 0)
    throw new Error('固定 knownTxids 用例缺少真实入口观察')
  for (const call of entry.paymentCalls) call.bodyText = await call.bodyText
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId: 'call-0',
    value: { kind: 'AuthFetch.knownTxidsInput', ...entry } }) + '\n')
  observed.delete(caseId)
})
