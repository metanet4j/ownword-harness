// 原 validateCertificates.test.ts：记录传入消息和 mock 验签/解密的真实响应。
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const cases = new Map([
  ['validateCertificates completes without errors for valid input', '07a5dbdce1f6d9f8c7cf13e2e2c12109004de34ab68186fde3e000b0910ee7d0'],
  ['validateCertificates throws an error for mismatched identity key', '8f2b06fb4bac7d2fa27c954289f66801fb2040eea34809930de969d622eac12a'],
  ['validateCertificates throws an error if certificate signature is invalid', '50be58fc7e604324292df73350ecd0407df30f4cc622793d9b306637944b7fae'],
  ['validateCertificates throws an error for unrequested certifier', '277465f431806550f2d40562615e591d2abc0a0e60c577cd3f04bc976dfd3ffd'],
  ['validateCertificates throws an error for unrequested certificate type', 'a3395b245234950d0b1f062970584e44ecd349cd7dd90dc49bc9655e879db1ae'],
  ['validateCertificates decrypts fields without throwing errors', 'd7c84d782a644801d5697f2676a786714ad43a1999e2d3bd26bfe8b2cc67a9d2'],
  ['validateCertificates throws an error if a field decryption fails', '1800d7778017c44690035a8d2505605c296b0b79e6d4724aa21e6515e9f8305d'],
  ['validateCertificates handles multiple certificates properly', '4c3b952ad3546f2aa72a27b21cc960ae4cf10925bc9346822aefec05fe0b44c5']
])

function record(caseId, sampleId, value) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId, value }) + '\n')
}

function observed(method, operation, caseId, sampleId) {
  return jest.fn((...args) => Promise.resolve().then(() => Reflect.apply(operation, this, args)).then(
    value => { record(caseId, sampleId, { kind: method, outcome: { kind: 'return', value } }); return value },
    error => { record(caseId, sampleId, { kind: method, outcome: { kind: 'throw', name: error.name, message: error.message } }); throw error }
  ))
}

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/utils/validateCertificates.ts')
const verifiablePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/certificates/VerifiableCertificate.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  return { ...actual, validateCertificates: async (wallet, message, requested, originator) => {
    const caseId = cases.get(expect.getState().currentTestName)
    if (!caseId) throw new Error('出现范围外的证书验证用例')
    const rootKey = wallet?.keyDeriver?.rootKey
    record(caseId, 'invocation', { kind: 'validateCertificates', walletIdentityKey: rootKey.toPublicKey().toString(),
      message, certificatesRequested: requested === undefined ? null : requested,
      originator: originator === undefined ? null : originator })
    const Constructor = jest.requireMock(verifiablePath).VerifiableCertificate
    const original = Constructor.getMockImplementation()
    let instanceIndex = 0
    Constructor.mockImplementation((...args) => {
      const instance = original(...args)
      const index = instanceIndex++
      instance.verify = observed('verify', instance.verify, caseId, `verify-${index}`)
      instance.decryptFields = observed('decryptFields', instance.decryptFields, caseId, `decrypt-${index}`)
      return instance
    })
    try { return await actual.validateCertificates(wallet, message, requested, originator) }
    finally { Constructor.mockImplementation(original) }
  } }
})
