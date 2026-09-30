// 固定原测试：采集 ScriptEvaluationError 构造函数实际收到的完整参数。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')

const task = __dirname
const file = 'src/script/__tests/ScriptEvaluationError.test.ts'
const catalog = JSON.parse(fs.readFileSync(path.join(task, 'module-tests.json'), 'utf8'))
const frozen = catalog.files.find(item => item.path === file)
if (!frozen || frozen.cases.length !== 9) throw new Error('固定脚本错误用例清单不符')
const ids = new Map(frozen.cases.map(item => [item.names.join(' '), item.id]))
let calls = 0
beforeEach(() => { calls = 0 })

function snapshot (value, depth = 0) {
  if (depth > 8) throw new Error('脚本错误参数层级超过采集边界')
  if (value === undefined) return { kind: 'Undefined' }
  if (value === null) return { kind: 'Null' }
  if (typeof value === 'number') return { kind: 'Number', value: String(value) }
  if (typeof value === 'string') return { kind: 'String', value }
  if (typeof value === 'boolean') return { kind: 'Boolean', value }
  if (Array.isArray(value)) return { kind: 'Array', values: value.map(item => snapshot(item, depth + 1)) }
  if (Object.getPrototypeOf(value) === Object.prototype) {
    return { kind: 'Object', fields: Object.fromEntries(Object.entries(value).map(([key, item]) => [key, snapshot(item, depth + 1)])) }
  }
  throw new Error(`脚本错误参数类型尚未表征：${value?.constructor?.name || typeof value}`)
}

function record (params) {
  const name = expect.getState().currentTestName
  const caseId = ids.get(name)
  if (!caseId) throw new Error(`非固定脚本错误用例：${name}`)
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId,
    sampleId: `constructor-${calls++}`,
    value: { kind: 'ScriptEvaluationError.constructor', params: snapshot(params) } }) + '\n')
}

const modulePath = path.resolve(task, '../../../reference/ts-stack/packages/sdk/src/script/ScriptEvaluationError.ts')
jest.doMock(modulePath, () => {
  const original = jest.requireActual(modulePath)
  return { ...original, default: new Proxy(original.default, {
    construct (target, args, newTarget) {
      if (args.length !== 1) throw new Error('原构造调用参数数量改变')
      record(args[0])
      return Reflect.construct(target, args, newTarget)
    }
  }), __esModule: true }
})
