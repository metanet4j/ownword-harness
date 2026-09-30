// 固定 Certificate.test.ts：在原 Jest 运行时观察熵、构造和签名/验证入口。
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const identifiers = [
  'e8b66126d21454f747bb9f00b97b085f074325b29dd2703778b82013507b69d8',
  '2246bd1a527a2e8517221f1de658ce49a93e4b9863c913aa69ad1482e775120b',
  '34cd68ff9e9505194c110eb95afafd968f04e51e3b7505623cf93b86a04c8e86',
  '1d2196c8be4c42410c827f935e9b016a6abc19316b27719f66afe844c70f2ca9',
  '045278fb2257782ced9049d59cc98e55e5ddc204e2d21b2f02a386df72a594ff',
  '5a3ae11b39819d617b0d1bd095ef04525815d16224ec88ebab4ca6941b9dc5ca',
  '8fdbcb89080c5c7d7a25e50171dccb7533350de366d966877d609c907016bdef',
  '250b89d07965dfa75bfa77282ba497024ecb7c512b64ac6ce068a49df55c9aff',
  '760a39a07db5ca9629f6afe9af2cd886e82f12fad717fbd7b7fb2bd4bd11e4a3',
  '91d7b28b912babc447df41cf219fb197f86b10f4b1171307372af640185236df',
  '08de563f5c5d36ac5eb9b4f7a2e7effa5684cfeea2efac5239d0fe2fd15ead83',
  '9edf2d8cd7bfc281f68c01d368ce82424490a8ea972b78ffd9d398494d294374',
  '4088cc12a4513718a204525e9cdf8eeba07fe78701e35a59f69f10c8fefaca03',
  'fe290bf3642f450334d1e21d96bf4168928cb8b85f855a4124a9d744fa5952b2',
  '00b20e32a76fe0d6773933dca70fa31410aba1a74ccde26c69b3c4f8ccd1e642'
]
const titles = [
  'should construct a Certificate with valid data',
  'should serialize and deserialize the Certificate without signature',
  'should serialize and deserialize the Certificate with signature',
  'should sign the Certificate and verify the signature successfully',
  'should fail verification if the Certificate is tampered with',
  'should fail verification if the signature is missing',
  'should fail verification if the signature is incorrect',
  'should handle certificates with empty fields',
  'should correctly handle serialization/deserialization when signature is excluded',
  'should correctly handle certificates with long field names and values',
  'should correctly serialize and deserialize the revocationOutpoint',
  'should correctly handle certificates with no fields',
  "should throw if already signed, and should update the certifier field if it differs from the wallet's public key",
  'should create a Certificate from an object using fromObject()',
  'should create a Certificate from an object without signature using fromObject()'
]
const cases = new Map(titles.map((title, index) => [`Certificate ${title}`, identifiers[index]]))
const counts = new Map()
let randomState = 0x243f6a88
let seedIndex = 0

function current() { return cases.get(expect.getState().currentTestName) }
function record(caseId, sampleId, value) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId, value }) + '\n')
}
function observed(kind, value) {
  const caseId = current()
  if (!caseId) throw new Error(`范围外的证书 ${kind} 调用`)
  const key = `${caseId}:${kind}`
  const index = counts.get(key) || 0
  counts.set(key, index + 1)
  record(caseId, `${kind}-${index}`, value)
}
function certificate(c) {
  return { type: c.type, serialNumber: c.serialNumber, subject: c.subject,
    certifier: c.certifier, revocationOutpoint: c.revocationOutpoint,
    fields: c.fields, signature: c.signature === undefined ? null : c.signature }
}

const originalCrypto = globalThis.crypto
const entropy = { subtle: originalCrypto?.subtle }
Object.defineProperty(entropy, 'getRandomValues', { value(array) {
  for (let index = 0; index < array.length; index++) {
    randomState ^= randomState << 13
    randomState ^= randomState >>> 17
    randomState ^= randomState << 5
    array[index] = randomState >>> 24
  }
  const caseId = current() || identifiers[0]
  record(caseId, `random-${seedIndex++}`, { kind: 'Random', length: array.length,
    bytesHex: Buffer.from(array).toString('hex') })
  return array
} })
Object.defineProperty(globalThis, 'crypto', { configurable: true, value: entropy })

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/certificates/Certificate.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Certificate = actual.default
  const sign = Certificate.prototype.sign
  const verify = Certificate.prototype.verify
  Certificate.prototype.sign = function (wallet) {
    observed('sign', { kind: 'Certificate.sign', certificate: certificate(this),
      walletIdentityKey: wallet.keyDeriver.rootKey.toPublicKey().toString() })
    return Reflect.apply(sign, this, [wallet])
  }
  Certificate.prototype.verify = function () {
    observed('verify', { kind: 'Certificate.verify', certificate: certificate(this) })
    return Reflect.apply(verify, this, [])
  }
  return { ...actual, __esModule: true, default: new Proxy(Certificate, {
    construct(target, args, newTarget) {
      observed('constructor', { kind: 'Certificate.constructor',
        type: args[0], serialNumber: args[1], subject: args[2], certifier: args[3],
        revocationOutpoint: args[4], fields: args[5],
        signature: args[6] === undefined ? null : args[6] })
      return Reflect.construct(target, args, newTarget)
    },
    get(target, key, receiver) {
      if (key === 'fromBinary') return bin => {
        observed('fromBinary', { kind: 'Certificate.fromBinary', bytesHex: Buffer.from(bin).toString('hex') })
        return target.fromBinary(bin)
      }
      if (key === 'fromObject') return object => {
        observed('fromObject', { kind: 'Certificate.fromObject', object })
        return target.fromObject(object)
      }
      return Reflect.get(target, key, receiver)
    }
  }) }
})
