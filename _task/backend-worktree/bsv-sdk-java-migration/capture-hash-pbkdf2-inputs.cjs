// 固定 Hash.test.ts 的 PBKDF2 向量：记录公开入口实际收到的字节和参数。
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS PBKDF2 采集环境')

const task = __dirname
const file = 'src/primitives/__tests/Hash.test.ts'
const catalog = JSON.parse(fs.readFileSync(path.join(task, 'module-tests.json'), 'utf8'))
const frozen = catalog.files.find(item => item.path === file)
const ids = new Map(frozen.cases.filter(item => item.names.some(name => name.startsWith('Passes PBKDF2 vector ')))
  .map(item => [item.names.join(' '), item.id]))
if (ids.size !== 13) throw new Error('固定 PBKDF2 向量用例清单不符')
let callIndex = 0
beforeEach(() => { callIndex = 0 })

function record(value) {
  const name = expect.getState().currentTestName
  const caseId = ids.get(name)
  if (!caseId) throw new Error(`PBKDF2 调用不属于固定向量用例：${name}`)
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId,
    sampleId: `call-${callIndex++}`, value }) + '\n')
}

const modulePath = path.resolve(task, '../../../reference/ts-stack/packages/sdk/src/primitives/Hash.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  return { ...actual,
    pbkdf2(key, salt, iterations, dkLen) {
      record({ kind: 'Hash.pbkdf2', keyHex: Buffer.from(key).toString('hex'),
        saltHex: Buffer.from(salt).toString('hex'), iterations, dkLen })
      return actual.pbkdf2(key, salt, iterations, dkLen)
    }
  }
})
