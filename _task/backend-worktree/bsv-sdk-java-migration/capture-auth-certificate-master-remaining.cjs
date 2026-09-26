// 固定 MasterCertificate.test.ts 余下 13 例：观察真实熵、共享夹具及公开 API 输入。
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const cases = new Map([
  ['MasterCertificate decryptFields (static) should decrypt all fields correctly using subject wallet', '0e7dd96cdd2e143612675c415fca4e3d9bea4550c777d84a5f1375587e8264b0'],
  ['MasterCertificate decryptFields (static) should throw if masterKeyring is empty or invalid', '666d1d1f6716c2f6cd16c0dc01c1a2f61ef94fd160fd55f00acbc6949c7c32ba'],
  ['MasterCertificate decryptFields (static) should throw if decryption fails for any field', '420aca9301ad8764b2726d8a668db3bbc45248c7e709c16ab61f665dbd4df9c1'],
  ['MasterCertificate createKeyringForVerifier (static) should create a verifier keyring for specified fields', 'e9da673d256fd3040959d6d8c42da9aa8b9681854e4270980d9b3da1d3a0d492'],
  ['MasterCertificate createKeyringForVerifier (static) should throw if fields to reveal are not a subset of the certificate fields', '87317252793bad20e1b3463ebf23b471e5ce591b09b40fc3a0fcb3b6862cf1af'],
  ['MasterCertificate createKeyringForVerifier (static) should throw if the master key fails to decrypt the corresponding field', 'afba597b37f51d1e0d010483d21d2dba94d95e5605d7cca7325db10720f4b884'],
  ['MasterCertificate createKeyringForVerifier (static) should support optional originator parameter', 'e67ff8bc289b7162fb8e66a0d4ef9656389efdb856100741c13123ad8d3edc8b'],
  ['MasterCertificate createKeyringForVerifier (static) should support counterparty of "anyone" or "self"', 'caad8325cd99a5a3d51b90549d61ea014f7ee5dfe7d07fcb9d168b31e0bee3cb'],
  ['MasterCertificate issueCertificateForSubject (static) should issue a valid MasterCertificate for the given subject', '45100bdfc38832d5200e292bfb3becd5278d5be3828af122a2cfa70d845e4799'],
  ['MasterCertificate issueCertificateForSubject (static) should allow passing a custom serial number when issuing the certificate', '81c307b349b1b2035e7d3b8e5ae9f75e22bd1737a4a6444dcebd03386ff29340'],
  ['MasterCertificate issueCertificateForSubject (static) should allow issuing a self-signed certificate and decrypt it with the same wallet', '25e78fa9c066d5e863141be7c0f65855fc1882ea11b2972b11d97c2c23745e9a'],
  ['MasterCertificate issueCertificateForSubject (static) resolves subject === "self" to the certifier wallet identity key', '5ce8ce6188f72cf2ce4aefe5e546822786b42ae8e2982e6948666b87362bedc9'],
  ['MasterCertificate issueCertificateForSubject (static) uses provided subjectIdentityKey when subject is a valid hex string', 'b3c040360d1fced69eb77fc6ac19c54839200ede25faf85dcbc0356e8aa5b464']
])
const setupCase = 'e9da673d256fd3040959d6d8c42da9aa8b9681854e4270980d9b3da1d3a0d492'
let active = null
let setupCapture = false
let randomState = 0x243f6a88
const counts = new Map()
const originalCrypto = globalThis.crypto
const entropy = { subtle: originalCrypto?.subtle }

beforeEach(() => { active = cases.get(expect.getState().currentTestName) || null; setupCapture = false })
afterEach(() => {
  setupCapture = active === '420aca9301ad8764b2726d8a668db3bbc45248c7e709c16ab61f665dbd4df9c1'
  active = null
})

function caseId() { return active || setupCase }
function record(id, sampleId, value) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId: id, sampleId, value }) + '\n')
}
function observed(kind, value) {
  const id = caseId()
  const key = `${id}:${kind}`
  const index = counts.get(key) || 0
  counts.set(key, index + 1)
  record(id, `${kind}-${index}`, value)
}
function walletIdentity(wallet) { return wallet.keyDeriver.rootKey.toPublicKey().toString() }
function certificate(cert) {
  return { type: cert.type, serialNumber: cert.serialNumber, subject: cert.subject,
    certifier: cert.certifier, revocationOutpoint: cert.revocationOutpoint, fields: cert.fields,
    masterKeyring: cert.masterKeyring, signature: cert.signature === undefined ? null : cert.signature }
}

Object.defineProperty(entropy, 'getRandomValues', { value(array) {
  for (let index = 0; index < array.length; index++) {
    randomState ^= randomState << 13
    randomState ^= randomState >>> 17
    randomState ^= randomState << 5
    array[index] = randomState >>> 24
  }
  if (active || setupCapture) {
    // beforeAll 的共享 issuedCert 属于第一条 createKeyring 用例。
    observed('random', { kind: 'Random', length: array.length, bytesHex: Buffer.from(array).toString('hex') })
  }
  return array
} })
Object.defineProperty(globalThis, 'crypto', { configurable: true, value: entropy })

const masterPath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/certificates/MasterCertificate.ts')
jest.doMock(masterPath, () => {
  const actual = jest.requireActual(masterPath)
  const Master = actual.MasterCertificate
  return { ...actual, MasterCertificate: new Proxy(Master, {
    construct(target, args, newTarget) {
      if (active) observed('constructor', { kind: 'MasterCertificate.constructor', type: args[0],
        serialNumber: args[1], subject: args[2], certifier: args[3], revocationOutpoint: args[4],
        fields: args[5], masterKeyring: args[6], signature: args[7] === undefined ? null : args[7] })
      return Reflect.construct(target, args, newTarget)
    },
    get(target, key, receiver) {
      if (key === 'issueCertificateForSubject') return (...args) => {
        const original = args[4]
        observed('issue', { kind: 'MasterCertificate.issueCertificateForSubject',
          walletIdentityKey: walletIdentity(args[0]), subject: args[1], fields: args[2], type: args[3],
          hasRevocationCallback: typeof original === 'function',
          serialNumber: args[5] === undefined ? null : args[5] })
        if (typeof original === 'function') args[4] = async (...callbackArgs) => {
          const result = await original(...callbackArgs)
          observed('revocation', { kind: 'revocationCallback', serialNumber: callbackArgs[0], result })
          return result
        }
        return Promise.resolve(Reflect.apply(target[key], target, args)).then(value => {
          observed('issueResult', { kind: 'MasterCertificate.issueResult', certificate: certificate(value) })
          return value
        })
      }
      if (key === 'decryptFields') return (...args) => {
        observed('decrypt', { kind: 'MasterCertificate.decryptFields',
          walletIdentityKey: walletIdentity(args[0]), masterKeyring: args[1], fields: args[2],
          counterparty: args[3], privileged: args[4] === undefined ? null : args[4],
          privilegedReason: args[5] === undefined ? null : args[5] })
        return Reflect.apply(target[key], target, args)
      }
      if (key === 'createKeyringForVerifier') return (...args) => {
        observed('keyring', { kind: 'MasterCertificate.createKeyringForVerifier',
          walletIdentityKey: walletIdentity(args[0]), certifier: args[1], verifier: args[2],
          fields: args[3], fieldsToReveal: args[4], masterKeyring: args[5], serialNumber: args[6],
          privileged: args[7] === undefined ? null : args[7],
          privilegedReason: args[8] === undefined ? null : args[8] })
        return Reflect.apply(target[key], target, args)
      }
      return Reflect.get(target, key, receiver)
    }
  }) }
})

const verifiablePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/certificates/VerifiableCertificate.ts')
jest.doMock(verifiablePath, () => {
  const actual = jest.requireActual(verifiablePath)
  const Verifiable = actual.VerifiableCertificate
  const decrypt = Verifiable.prototype.decryptFields
  Verifiable.prototype.decryptFields = function (wallet) {
    if (active) observed('verifiableDecrypt', { kind: 'VerifiableCertificate.decryptFields',
      walletIdentityKey: walletIdentity(wallet), type: this.type, serialNumber: this.serialNumber,
      subject: this.subject, certifier: this.certifier, revocationOutpoint: this.revocationOutpoint,
      fields: this.fields, keyring: this.keyring, signature: this.signature === undefined ? null : this.signature })
    return Reflect.apply(decrypt, this, [wallet])
  }
  return { ...actual, VerifiableCertificate: new Proxy(Verifiable, {
    construct(target, args, newTarget) {
      if (active) observed('verifiableConstructor', { kind: 'VerifiableCertificate.constructor',
        type: args[0], serialNumber: args[1], subject: args[2], certifier: args[3],
        revocationOutpoint: args[4], fields: args[5], keyring: args[6],
        signature: args[7] === undefined ? null : args[7] })
      return Reflect.construct(target, args, newTarget)
    }
  }) }
})
