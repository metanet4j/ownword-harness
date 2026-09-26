// 固定 AuthFetch 原测试中付款上下文与标签输入、钱包 mock 返回的真实轨迹。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const plan = require('./auth-fetch-primary-context-labels-plan.json')
const catalog = require('./module-tests.json')
const file = catalog.files.find(item => item.path === 'src/auth/clients/__tests__/AuthFetch.test.ts')
const cases = new Map(file.cases.filter(item => Object.hasOwn(plan, item.id))
  .map(item => [item.names.join(' '), item.id]))
if (cases.size !== 3) throw new Error('固定付款上下文/标签用例身份变化')

function record(caseId, value) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId: 'call-0', value }) + '\n')
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
const noncePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/utils/createNonce.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const context = actual.AuthFetch.prototype.createPaymentContext
  const labels = actual.AuthFetch.prototype.buildPaymentActionLabels
  actual.AuthFetch.prototype.createPaymentContext = function (...arguments_) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (!caseId) return Reflect.apply(context, this, arguments_)
    const [url, config, satoshisRequired, serverIdentityKey, derivationPrefix, knownTxids] = arguments_
    const wallet = this.wallet
    const nonceMock = jest.requireMock(noncePath).createNonce
    const starts = { nonce: nonceMock.mock.calls.length,
      keys: wallet.getPublicKey.mock.calls.length,
      action: wallet.createAction.mock.calls.length }
    const input = { url, config: JSON.parse(JSON.stringify(config)), satoshisRequired,
      serverIdentityKey, derivationPrefix,
      knownTxids: arguments_.length < 6 ? { type: 'undefined' } : knownTxids }
    return Promise.resolve(Reflect.apply(context, this, arguments_)).then(async value => {
      const nonce = await nonceMock.mock.results[starts.nonce].value
      const publicKeys = await Promise.all(wallet.getPublicKey.mock.results
        .slice(starts.keys).map(result => result.value))
      const action = await wallet.createAction.mock.results[starts.action].value
      if (publicKeys.length !== 2 || wallet.createAction.mock.calls.length !== starts.action + 1)
        throw new Error('固定钱包 mock 调用次数变化')
      record(caseId, { kind: 'AuthFetch.paymentContextInput', input,
        mockReturns: { nonce, publicKeys, createActionTx: Array.from(action.tx) } })
      return value
    })
  }
  actual.AuthFetch.prototype.buildPaymentActionLabels = function (...arguments_) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (caseId && file.cases.find(item => item.id === caseId).names.at(-1)
        === 'brc105 payment label hex survives lowercasing and round-trips to base64') {
      const [config, prefix, suffix] = arguments_
      record(caseId, { kind: 'AuthFetch.paymentLabelInput',
        input: { config: JSON.parse(JSON.stringify(config)), prefix, suffix } })
    }
    return Reflect.apply(labels, this, arguments_)
  }
  return actual
})
