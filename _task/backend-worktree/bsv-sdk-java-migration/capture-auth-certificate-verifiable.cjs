// 固定 VerifiableCertificate.test.ts：观察逐例熵、构造、解密和转换的真实输入。
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const cases = new Map([
  ['VerifiableCertificate constructor should create a VerifiableCertificate with all required properties', 'b48b53672f8f0ed3ebd899a82832de3bc581504e72cfeac572124d861ddeb385'],
  ['VerifiableCertificate decryptFields should decrypt fields successfully when provided the correct verifier wallet and keyring', '6c595c672ed00e550169ffc31b7a748931e728b345b07290752bbf45c67f1668'],
  ['VerifiableCertificate decryptFields should fail if the verifier wallet does not have the correct private key (wrong key)', 'ffa0cd31bf3196a285b20b0f7224b019f968ae949bdb39b5262c241bdfb3b108'],
  ['VerifiableCertificate decryptFields should fail if the keyring is empty or missing keys', 'e01bc963dc5b0ac6a487c5ee7adf38407cd8216b4fd76a3c65fa0b756aa2bc55'],
  ['VerifiableCertificate decryptFields should fail if the encrypted field or its key is tampered', 'ad01265b4bb62b07bd6163f3287bd37323a7f46f28a12a6029e4f266cd23eea2'],
  ['VerifiableCertificate decryptFields should be able to decrypt fields using the anyone wallet', '9e098e9d7cda799e770c4563c5564ed717dcb4db75d0996a63c8171a8977c7d0'],
  ['VerifiableCertificate fromCertificate should create an equivalent VerifiableCertificate and decrypt correctly', '96b539a0963ab9d68cdb4117c0962e3c7c912fd682f004816bfa8edc175905b2']
])
let randomState = 0x243f6a88
let randomIndex = 0
const counts = new Map()
const originalCrypto = globalThis.crypto
const entropy = { subtle: originalCrypto?.subtle }

function current() { return cases.get(expect.getState().currentTestName) }
function record(caseId, sampleId, value) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId, value }) + '\n')
}
function observed(kind, value) {
  const caseId = current()
  if (!caseId) throw new Error(`范围外的可验证证书 ${kind} 调用`)
  const key = `${caseId}:${kind}`
  const index = counts.get(key) || 0
  counts.set(key, index + 1)
  record(caseId, `${kind}-${index}`, value)
}
function certificate(c) {
  return { type: c.type, serialNumber: c.serialNumber, subject: c.subject, certifier: c.certifier,
    revocationOutpoint: c.revocationOutpoint, fields: c.fields, keyring: c.keyring,
    signature: c.signature === undefined ? null : c.signature }
}
function walletIdentity(wallet) {
  const root = wallet?.keyDeriver?.rootKey
  return root?.toPublicKey?.().toString() || (root === 'anyone' ? 'anyone' : null)
}

Object.defineProperty(entropy, 'getRandomValues', { value(array) {
  for (let index = 0; index < array.length; index++) {
    randomState ^= randomState << 13
    randomState ^= randomState >>> 17
    randomState ^= randomState << 5
    array[index] = randomState >>> 24
  }
  const caseId = current()
  if (caseId) record(caseId, `random-${randomIndex++}`, { kind: 'Random', length: array.length,
    bytesHex: Buffer.from(array).toString('hex') })
  return array
} })
Object.defineProperty(globalThis, 'crypto', { configurable: true, value: entropy })
beforeEach(() => { randomState = 0x243f6a88; randomIndex = 0 })

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/certificates/VerifiableCertificate.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Certificate = actual.VerifiableCertificate
  const decrypt = Certificate.prototype.decryptFields
  Certificate.prototype.decryptFields = function (wallet, privileged, reason, originator) {
    observed('decrypt', { kind: 'VerifiableCertificate.decryptFields', certificate: certificate(this),
      walletIdentityKey: walletIdentity(wallet), privileged: privileged === undefined ? null : privileged,
      reason: reason === undefined ? null : reason, originator: originator === undefined ? null : originator })
    return Reflect.apply(decrypt, this, [wallet, privileged, reason, originator])
  }
  return { ...actual, VerifiableCertificate: new Proxy(Certificate, {
    construct(target, args, newTarget) {
      observed('constructor', { kind: 'VerifiableCertificate.constructor', type: args[0],
        serialNumber: args[1], subject: args[2], certifier: args[3], revocationOutpoint: args[4],
        fields: args[5], keyring: args[6], signature: args[7] === undefined ? null : args[7] })
      return Reflect.construct(target, args, newTarget)
    },
    get(target, key, receiver) {
      if (key === 'fromCertificate') return (base, keyring) => {
        observed('fromCertificate', { kind: 'VerifiableCertificate.fromCertificate',
          certificate: { type: base.type, serialNumber: base.serialNumber, subject: base.subject,
            certifier: base.certifier, revocationOutpoint: base.revocationOutpoint, fields: base.fields,
            signature: base.signature === undefined ? null : base.signature }, keyring })
        return target.fromCertificate(base, keyring)
      }
      return Reflect.get(target, key, receiver)
    }
  }) }
})
