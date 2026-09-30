// 固定原 MasterCertificate.test.ts 的构造测试：记录实际熵字节和传给构造器的参数。
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const cases = new Map([
  ['MasterCertificate constructor should construct a MasterCertificate successfully when masterKeyring is valid',
    '13b4b968a38bc16a436bda799dabd933901d1802c28b8eb3e898e12ef11772f4'],
  ['MasterCertificate constructor should throw if masterKeyring is missing a key for any field',
    '7255afac01b0569e34c3fc01905bbda39c7f56a64f256bc85ed1dbb65fe3594e']
])

let state = 0x243f6a88
let randomIndex = 0
const originalCrypto = globalThis.crypto
const crypto = { subtle: originalCrypto?.subtle }

function record(caseId, sampleId, value) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId, value }) + '\n')
}

Object.defineProperty(crypto, 'getRandomValues', { value(array) {
  for (let index = 0; index < array.length; index++) {
    state ^= state << 13
    state ^= state >>> 17
    state ^= state << 5
    array[index] = state >>> 24
  }
  const caseId = cases.get(expect.getState().currentTestName)
  if (caseId) record(caseId, `random-${randomIndex++}`, {
    kind: 'Random', length: array.length, bytesHex: Buffer.from(array).toString('hex')
  })
  return array
} })
Object.defineProperty(globalThis, 'crypto', { configurable: true, value: crypto })

beforeEach(() => { state = 0x243f6a88; randomIndex = 0 })

const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/certificates/MasterCertificate.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  return { ...actual, MasterCertificate: new Proxy(actual.MasterCertificate, {
    construct(target, args, newTarget) {
      const caseId = cases.get(expect.getState().currentTestName)
      if (caseId) {
        const [type, serialNumber, subject, certifier, revocationOutpoint, fields, masterKeyring, signature] = args
        record(caseId, 'constructor', { kind: 'MasterCertificate.constructor',
          type, serialNumber, subject, certifier, revocationOutpoint, fields, masterKeyring,
          signature: signature === undefined ? null : signature })
      }
      return Reflect.construct(target, args, newTarget)
    }
  }) }
})
