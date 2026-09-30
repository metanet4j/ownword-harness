// 记录固定 Script/Spend 原测试实际传入 SDK 的参数；不修改固定 TS 文件。
const fs = require('node:fs')
const path = require('node:path')
const nativeExpect = global.expect
const catalog = JSON.parse(fs.readFileSync(process.env.MIGRATION_VECTOR_CATALOG, 'utf8'))
const output = process.env.MIGRATION_VECTOR_TS_INPUTS
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮向量采集身份')
const testPath = nativeExpect.getState().testPath
const source = catalog.files.find(file => testPath.endsWith('/' + file.path))
if (!source) throw new Error('不属于固定向量测试文件')
const names = new Map(source.cases.map(row => [row.names.join(' ') + '\0' + row.occurrence, row.id]))
const occurrences = new Map()
let active
function append(input) {
  if (active) fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId: active,
    test: nativeExpect.getState().currentTestName, input }) + '\n')
}
beforeEach(() => {
  const name = nativeExpect.getState().currentTestName
  const count = (occurrences.get(name) || 0) + 1
  occurrences.set(name, count)
  active = names.get(name + '\0' + count)
  if (!active || !source.path.endsWith('/Script.test.ts')) return
  const Script = jest.requireActual(path.resolve(path.dirname(testPath), '../Script.ts')).default
  for (const method of ['fromHex', 'fromASM']) {
    const original = Script[method]
    jest.spyOn(Script, method).mockImplementation(function (...args) {
      if (args.length !== 1 || typeof args[0] !== 'string') throw new Error('固定 Script 参数形态变化')
      append({ method: 'Script.' + method, args })
      return Reflect.apply(original, this, args)
    })
  }
})
afterEach(() => { active = undefined; jest.restoreAllMocks() })

if (!source.path.endsWith('/Script.test.ts')) {
  const modulePath = path.resolve(path.dirname(testPath), '../Spend.ts')
  jest.doMock(modulePath, () => {
    // 在原测试完成 TS 转换后才加载实际模块，避免 setup 提前触发另一套转换配置。
    const actual = jest.requireActual(modulePath)
    return { ...actual, __esModule: true, default: new Proxy(actual.default, {
    construct(target, args, newTarget) {
      if (active) {
        if (args.length !== 1) throw new Error('固定 Spend 构造参数数量变化')
        const params = args[0]
        const fields = ['sourceTXID', 'sourceOutputIndex', 'sourceSatoshis', 'lockingScript',
          'transactionVersion', 'otherInputs', 'outputs', 'inputIndex', 'unlockingScript', 'inputSequence', 'lockTime']
        if (Object.keys(params).sort().join() !== fields.sort().join() ||
            params.otherInputs.length || params.outputs.length) throw new Error('固定 Spend 前置字段变化')
        const input = { sourceTXID: params.sourceTXID, lockingScriptHex: params.lockingScript.toHex(),
          unlockingScriptHex: params.unlockingScript.toHex(), otherInputs: [], outputs: [] }
        for (const field of ['sourceOutputIndex', 'sourceSatoshis', 'transactionVersion', 'inputIndex', 'inputSequence', 'lockTime']) {
          if (!Number.isSafeInteger(params[field])) throw new Error('固定 Spend 数值字段变化')
          input[field] = String(params[field])
        }
        append({ method: 'Spend.constructor', args: [input] })
      }
      return Reflect.construct(target, args, newTarget)
    }
    }) }
  })
}
