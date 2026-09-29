// spend 批 TS 探针共享库：按局部冻结清单过滤用例，记录入口实参，并提供与 Java
// 侧 `SpendObservation` 逐值一致的原语描述（脚本十六进制/ASM、输入输出、Spend 构造参数）。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

/** 数值统一规范成十进制字符串：两侧 JSON 数字类型不同也不影响逐值比较。 */
function jsNumber (value) {
  if (value === undefined || value === null) return null
  if (typeof value === 'bigint') return value.toString()
  if (typeof value !== 'number') return typeof value === 'string' ? value : String(value)
  if (Number.isNaN(value)) return 'NaN'
  if (!Number.isFinite(value)) return value > 0 ? 'Infinity' : '-Infinity'
  if (Object.is(value, -0)) return '0'
  return String(value)
}

function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  const mapped = name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name
  return { kind: 'throw', name: mapped,
    message: error && error.message !== undefined ? String(error.message) : null }
}

/**
 * 32 位整数投影：这些入口字段在 Java 侧是有符号 `int`（同一个 32 位模式，例如 0xffffffff 存成 -1，
 * 高位版本号被截断成负数），而 TS 的 number 没有位宽。两侧统一按同一 32 位模式的有符号十进制记录，
 * 与 Java SDK 自身的 `jsInt32`／`int` 口径一致；未传值时取该字段的实际生效值 0。
 */
function jsInt32 (value) {
  if (value === undefined || value === null) return '0'
  const numeric = Number(value)
  return Number.isFinite(numeric) ? String(numeric | 0) : jsNumber(value)
}

/** 金额类数值：Java 侧是 64 位 double，只把未传值规范成实际生效的 0，不做 32 位截断。 */
function jsSatoshis (value) {
  return value === undefined || value === null ? '0' : jsNumber(value)
}

function describeScript (script) {
  if (script === null || script === undefined) return null
  return { asm: script.toASM(), hex: script.toHex() }
}

function describeInput (item) {
  if (item === null || item === undefined) return null
  return { sourceTXID: item.sourceTXID === undefined ? null : item.sourceTXID,
    sourceOutputIndex: jsInt32(item.sourceOutputIndex),
    unlockingScript: describeScript(item.unlockingScript),
    sequence: item.sequence === undefined ? null : jsNumber(item.sequence),
    hasTemplate: typeof item.unlockingScriptTemplate === 'object' && item.unlockingScriptTemplate !== null,
    hasSourceTransaction: typeof item.sourceTransaction === 'object' && item.sourceTransaction !== null }
}

function describeOutput (item) {
  if (item === null || item === undefined) return null
  return { satoshis: item.satoshis === undefined ? null : jsNumber(item.satoshis),
    lockingScript: describeScript(item.lockingScript),
    change: item.change === undefined ? null : item.change }
}

function describeFlags (flags) {
  if (flags === undefined || flags === null) return null
  const list = Array.isArray(flags) ? flags : String(flags).split(',')
  return Array.from(new Set(list.map(flag => String(flag).trim()).filter(flag => flag.length > 0))).sort()
}

/** Spend 构造参数的可比对投影；Java 侧 `SpendObservation.spendParams` 必须逐字段一致。 */
function describeSpendParams (params) {
  const allInputs = params.allInputs === undefined || params.allInputs === null ? null : params.allInputs
  return { sourceTXID: params.sourceTXID === undefined ? null : params.sourceTXID,
    sourceOutputIndex: jsInt32(params.sourceOutputIndex),
    sourceSatoshis: jsNumber(params.sourceSatoshis),
    transactionVersion: jsInt32(params.transactionVersion),
    inputIndex: jsNumber(params.inputIndex),
    inputSequence: jsNumber(params.inputSequence),
    lockTime: jsNumber(params.lockTime),
    memoryLimit: params.memoryLimit === undefined ? null : jsNumber(params.memoryLimit),
    isRelaxed: params.isRelaxed === true,
    verifyFlags: describeFlags(params.verifyFlags),
    hasSigHashCache: params.sigHashCache !== undefined && params.sigHashCache !== null,
    lockingScript: describeScript(params.lockingScript),
    unlockingScript: describeScript(params.unlockingScript),
    otherInputs: (params.otherInputs || []).map(describeInput),
    outputs: (params.outputs || []).map(describeOutput),
    allInputs: allInputs === null ? null : allInputs.map(describeInput) }
}

/** 交易签名前置参数的可比对投影；Java 侧 `SpendObservation.signatureParams` 必须逐字段一致。 */
function describeSignatureParams (params) {
  return { sourceTXID: params.sourceTXID === undefined ? null : params.sourceTXID,
    sourceOutputIndex: jsInt32(params.sourceOutputIndex),
    sourceSatoshis: jsSatoshis(params.sourceSatoshis),
    transactionVersion: jsInt32(params.transactionVersion),
    otherInputs: (params.otherInputs || []).map(describeInput),
    outputs: (params.outputs || []).map(describeOutput),
    inputIndex: jsNumber(params.inputIndex),
    subscript: describeScript(params.subscript),
    inputSequence: jsNumber(params.inputSequence === undefined ? 0xffffffff : params.inputSequence),
    lockTime: jsNumber(params.lockTime),
    scope: jsInt32(params.scope),
    ignoreChronicle: params.ignoreChronicle === true }
}

/**
 * 建立绑定到本探针的采集器。options：
 *   output    本侧原始轨迹路径（探针自己的 MIGRATION_*_TS_OBSERVATIONS）
 *   label     报错用名称
 *   testPath  固定原测试文件绝对路径（expect.getState().testPath）
 * 冻结清单从 EVIDENCE_INPUT_PLAN 同目录的 catalog.json 读取，只登记本局部名下用例。
 */
function create (options) {
  const output = options.output
  if (!output) throw new Error('缺少 Spend 原输入采集路径：' + options.label)
  const plan = process.env.EVIDENCE_INPUT_PLAN
  if (!plan) throw new Error('缺少本轮固定输入计划：' + options.label)
  const catalog = JSON.parse(fs.readFileSync(path.join(path.dirname(plan), 'catalog.json'), 'utf8'))
  const testPath = options.testPath || expect.getState().testPath
  const source = catalog.files.find(file => testPath.endsWith('/' + file.path))
  if (!source) throw new Error('不属于固定 Spend 测试文件：' + options.label + ' / ' + testPath)
  const sdk = path.resolve(path.dirname(testPath), '../../..')
  const identities = new Map(source.cases.map(row => [row.names.join(' ') + '\0' + row.occurrence, row.id]))
  const occurrences = new Map()
  let active
  let sequence = 0
  let depth = 0

  function current () { return expect.getState().currentTestName }
  function line (pattern) {
    const match = new Error().stack.match(pattern)
    return match ? Number(match[1]) : null
  }
  function begin () {
    const test = current()
    const occurrence = (occurrences.get(test) || 0) + 1
    occurrences.set(test, occurrence)
    sequence = 0
    active = test === undefined ? undefined : identities.get(test + '\0' + occurrence)
  }
  function record (method, args, result, at = null) {
    if (!active) return
    fs.appendFileSync(output, JSON.stringify({ test: current(), occurrence: occurrences.get(current()),
      sequence: ++sequence, source: { file: path.relative(sdk, testPath).replaceAll(path.sep, '/'), line: at },
      method, args, result }) + '\n')
  }
  function observe (method, args, action, describe) {
    if (!active || depth !== 0) return action()
    depth++
    try {
      const result = action()
      record(method, args, describe === undefined || describe === null ? null : describe(result))
      return result
    } catch (error) {
      record(method, args, thrown(error))
      throw error
    } finally {
      depth--
    }
  }
  /** 与 observe 相同，但结果总是以 `null` 记录（构造类入口）。 */
  function spend (params) {
    const described = describeSpendParams(params)
    record('Spend.constructor', [described], null)
    return described
  }
  return { begin, record, observe, spend, current, line, describeScript,
    describeInput, describeOutput, describeSpendParams, describeSignatureParams, thrown, jsNumber,
    get active () { return active }, get sequence () { return sequence } }
}

/** 用一个只包装构造函数/静态方法的 Proxy 替换模块默认导出。 */
function proxyModule (modulePath, install) {
  jest.doMock(modulePath, () => {
    const moduleObject = jest.requireActual(modulePath)
    if (moduleObject.default === undefined) return moduleObject
    install(moduleObject.default)
    return moduleObject
  })
}

module.exports = { create, proxyModule, describeScript, describeInput, describeOutput,
  describeSpendParams, describeSignatureParams, describeFlags, thrown, jsNumber, jsInt32, jsSatoshis }
