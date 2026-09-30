// 固定 ChronicleOpcodes.test.ts 原输入：每个用例真实构造的 Spend 入参（与原向量同一口径）
// 以及 validate() 是否通过。Spend 与 Script／Transaction 互相引用，因此用真实模块只包装
// 构造函数与原型方法，且只安装一次，避免工厂重入时拿到半初始化模块。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_CHRONICLE_OPCODES_TS_OBSERVATIONS
if (!output) throw new Error('缺少 ChronicleOpcodes 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/script/Spend.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/ChronicleOpcodes\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('ChronicleOpcodes 入口缺少固定原测试调用位置')
  return Number(match[1])
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('ChronicleOpcodes 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function jsNumber (value, fallback) {
  if (value === undefined || value === null) return fallback
  if (typeof value === 'number') {
    return Number.isInteger(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER ? value : String(value)
  }
  return String(value)
}
function hex (script) { return script === null || script === undefined ? null : script.toHex() }
function scriptChunks (script) {
  if (script === null || script === undefined) return null
  return script.chunks.map(chunk => {
    const out = { op: chunk.op }
    if (chunk.data !== undefined) out.data = Array.from(chunk.data, value => value & 0xff)
    if (chunk.invalidLength === true) out.invalidLength = true
    return out
  })
}
function describeInput (item) {
  return { sourceTXID: item.sourceTXID ?? null,
    sourceOutputIndex: jsNumber(item.sourceOutputIndex, 0),
    unlockingScript: item.unlockingScript === undefined ? null : hex(item.unlockingScript),
    sequence: jsNumber(item.sequence, null) }
}
function describeOutput (item) {
  return { satoshis: jsNumber(item.satoshis, null), lockingScript: hex(item.lockingScript) }
}
// 与原 spends 向量同一字段口径：两侧都按同一序列化结果比较。
function describeParams (params) {
  return { sourceTXID: params.sourceTXID ?? null,
    sourceOutputIndex: jsNumber(params.sourceOutputIndex, 0),
    sourceSatoshis: jsNumber(params.sourceSatoshis, 0),
    lockingScript: hex(params.lockingScript),
    lockingChunks: scriptChunks(params.lockingScript),
    transactionVersion: jsNumber(params.transactionVersion, 0),
    otherInputs: (params.otherInputs ?? []).map(describeInput),
    outputs: (params.outputs ?? []).map(describeOutput),
    inputIndex: jsNumber(params.inputIndex, 0),
    unlockingScript: hex(params.unlockingScript),
    unlockingChunks: scriptChunks(params.unlockingScript),
    inputSequence: jsNumber(params.inputSequence, 0),
    lockTime: jsNumber(params.lockTime, 0),
    verifyFlags: params.verifyFlags === undefined ? null
      : (Array.isArray(params.verifyFlags) ? params.verifyFlags.slice() : String(params.verifyFlags)),
    isRelaxed: params.isRelaxed === true }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function install (Original) {
  const validateOriginal = Original.prototype.validate
  // 原断言只判定「成功」或「抛错」；输入侧只记这二值，异常身份与消息留给断言轨迹。
  Original.prototype.validate = function (...args) {
    let passed
    try {
      passed = Reflect.apply(validateOriginal, this, args) === true
    } catch (error) {
      record('Spend.validate', [], { kind: 'return', value: { type: 'boolean', value: false } })
      throw error
    }
    record('Spend.validate', [], { kind: 'return', value: { type: 'boolean', value: passed } })
    return passed
  }
  return new Proxy(Original, {
    construct (target, args, newTarget) {
      record('Spend.constructor', [describeParams(args[0])], null)
      return Reflect.construct(target, args, newTarget)
    }
  })
}

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  const Spend = install(moduleObject.default)
  return Object.assign({}, moduleObject, { default: Spend, __esModule: true })
})
