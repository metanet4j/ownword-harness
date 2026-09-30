// 原 getVerifiableCertificates.test.ts：记录函数入参与钱包 mock 实际返回/拒绝。
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const cases = new Map([
  ['getVerifiableCertificates retrieves matching certificates based on requested set', '68267687822c406ff8ca1d217aafab25bb741bb8d653768a39577ad6dab36a8d'],
  ['getVerifiableCertificates returns an empty array when no matching certificates are found', '1b5e01644c9b81baeb1069e38c2c589b16ff37a35949d89fbecf766f8713762e'],
  ['getVerifiableCertificates propagates errors from listCertificates', 'aee6df75d4f19e114ad19ce2943550c69bb85db813806a71c29a0b2e3097f4bc'],
  ['getVerifiableCertificates propagates errors from proveCertificate', 'e6d1846cc23c3a20c988060a45f5d51223871edf2d5412b56a2a1e9ae888cf61'],
  ['getVerifiableCertificates handles empty requested certificates gracefully', 'a27178e2f0295447da8083f40584616d8c5377e7f485bf1dd22357b30994c7ca']
])

function record(caseId, sampleId, value) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId, value }) + '\n')
}

function observe(wallet, method, caseId, sampleId) {
  const original = wallet[method]
  wallet[method] = function (...args) {
    let result
    try { result = Reflect.apply(original, this, args) }
    catch (error) {
      record(caseId, sampleId, { kind: method, outcome: { kind: 'throw', name: error.name, message: error.message } })
      throw error
    }
    return Promise.resolve(result).then(
      value => { record(caseId, sampleId, { kind: method, outcome: { kind: 'return', value } }); return value },
      error => { record(caseId, sampleId, { kind: method, outcome: { kind: 'throw', name: error.name, message: error.message } }); throw error }
    )
  }
  return original
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/utils/getVerifiableCertificates.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  return { ...actual, getVerifiableCertificates: async (wallet, requestedCertificates, verifierIdentityKey, originator) => {
    const caseId = cases.get(expect.getState().currentTestName)
    if (!caseId) throw new Error('出现范围外的证书获取用例')
    record(caseId, 'invocation', { kind: 'getVerifiableCertificates', requestedCertificates,
      verifierIdentityKey, originator: originator === undefined ? null : originator })
    const list = observe(wallet, 'listCertificates', caseId, 'listResponse')
    const prove = observe(wallet, 'proveCertificate', caseId, 'proveResponse')
    try { return await actual.getVerifiableCertificates(wallet, requestedCertificates, verifierIdentityKey, originator) }
    finally { wallet.listCertificates = list; wallet.proveCertificate = prove }
  } }
})
