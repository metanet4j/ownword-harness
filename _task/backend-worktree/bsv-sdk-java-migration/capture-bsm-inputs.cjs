// 固定 BSM.test.ts：在公开函数入口记录真实消息、密钥与签名输入。
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS BSM 采集环境')

const task = __dirname
const file = 'src/compat/__tests/BSM.test.ts'
const catalog = JSON.parse(fs.readFileSync(path.join(task, 'module-tests.json'), 'utf8'))
const frozen = catalog.files.find(item => item.path === file)
if (!frozen || frozen.cases.length !== 6) throw new Error('固定 BSM 用例清单不符')
const ids = new Map(frozen.cases.map(item => [item.names.join(' '), item.id]))
let callIndex = 0
beforeEach(() => { callIndex = 0 })

function hex(bytes) { return Buffer.from(bytes).toString('hex') }
function record(value) {
  const name = expect.getState().currentTestName
  const caseId = ids.get(name)
  if (!caseId) throw new Error(`BSM 调用不属于固定原用例：${name}`)
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId,
    sampleId: `call-${callIndex++}`, value }) + '\n')
}

const modulePath = path.resolve(task, '../../../reference/ts-stack/packages/sdk/src/compat/BSM.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  return { ...actual,
    magicHash(message) {
      record({ kind: 'BSM.magicHash', messageHex: hex(message) })
      return actual.magicHash(message)
    },
    sign(message, key, mode) {
      record({ kind: 'BSM.sign', messageHex: hex(message), keyHex: key.toString(),
        mode: mode === undefined ? 'undefined' : mode })
      return actual.sign(message, key, mode)
    },
    verify(message, signature, publicKey) {
      record({ kind: 'BSM.verify', messageHex: hex(message),
        signatureDerHex: hex(signature.toDER()), publicKeyDerHex: hex(publicKey.toDER()) })
      return actual.verify(message, signature, publicKey)
    }
  }
})
