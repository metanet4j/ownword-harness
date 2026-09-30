// 固定 TransactionSignature.additional.test.ts 原输入：构造/低 S 判断、解析入口与 formatter 的计划参数。
// TransactionSignature 与 Transaction 互相引用，因此用真实模块只包装原型/静态方法。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_TRANSACTION_SIGNATURE_TS_OBSERVATIONS
if (!output) throw new Error('缺少 TransactionSignature 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/primitives/TransactionSignature.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/TransactionSignature\.additional\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('TransactionSignature 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function observe (method, args, action, describe) {
  if (depth !== 0) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? null : describe(result))
    return result
  } catch (error) {
    record(method, args, thrown(error))
    throw error
  } finally {
    depth--
  }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function jsNumber (value) {
  return Number.isInteger(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER ? value : String(value)
}
function describeScript (script) {
  if (script === null || script === undefined) return null
  return { asm: script.toASM(), hex: script.toHex() }
}
function describeInput (item) {
  return { sourceTXID: item.sourceTXID ?? null,
    sourceOutputIndex: jsNumber(item.sourceOutputIndex ?? 0),
    sequence: item.sequence === undefined ? null : jsNumber(item.sequence),
    hasSourceTransaction: typeof item.sourceTransaction === 'object' && item.sourceTransaction !== null }
}
function describeOutput (item) {
  return { satoshis: item.satoshis === undefined ? null : jsNumber(item.satoshis),
    lockingScript: describeScript(item.lockingScript) }
}
function describeSignature (sig) {
  return { kind: 'signature', scope: jsNumber(sig.scope), r: String(sig.r), s: String(sig.s) }
}
function describeParams (params) {
  return { sourceTXID: params.sourceTXID ?? null,
    sourceOutputIndex: jsNumber(params.sourceOutputIndex ?? 0),
    sourceSatoshis: jsNumber(params.sourceSatoshis ?? 0),
    transactionVersion: jsNumber(params.transactionVersion ?? 0),
    otherInputs: (params.otherInputs ?? []).map(describeInput),
    outputs: (params.outputs ?? []).map(describeOutput),
    inputIndex: jsNumber(params.inputIndex ?? 0),
    subscript: describeScript(params.subscript),
    inputSequence: jsNumber(params.inputSequence ?? 0),
    lockTime: jsNumber(params.lockTime ?? 0),
    scope: jsNumber(params.scope ?? 0),
    hasCache: params.cache !== undefined && params.cache !== null,
    hasAllInputs: Array.isArray(params.allInputs),
    allInputs: Array.isArray(params.allInputs) ? params.allInputs.map(describeInput) : null }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function install (Original) {
  const originals = {}
  for (const method of ['hasLowS', 'toChecksigFormat']) originals[method] = Original.prototype[method]
  for (const method of ['fromChecksigFormat', 'formatBip143', 'formatBytes', 'formatOTDA']) originals[method] = Original[method]

  Original.prototype.hasLowS = function (...args) {
    return observe('hasLowS', [{ kind: 'receiver', value: describeSignature(this) }],
      () => Reflect.apply(originals.hasLowS, this, args), result => ({ kind: 'boolean', value: result }))
  }
  Original.prototype.toChecksigFormat = function (...args) {
    return observe('toChecksigFormat', [{ kind: 'receiver', value: describeSignature(this) }],
      () => Reflect.apply(originals.toChecksigFormat, this, args),
      result => ({ kind: 'numberArray', hex: hex(Uint8Array.from(result)), length: result.length }))
  }
  Original.fromChecksigFormat = function (...args) {
    return observe('fromChecksigFormat', [{ kind: 'bytes', hex: hex(Uint8Array.from(args[0])) }],
      () => Reflect.apply(originals.fromChecksigFormat, this, args), describeSignature)
  }
  for (const method of ['formatBip143', 'formatBytes', 'formatOTDA']) {
    Original[method] = function (...args) {
      return observe(method, [describeParams(args[0])],
        () => Reflect.apply(originals[method], this, args),
        result => ({ kind: 'bytes', hex: hex(Uint8Array.from(result)) }))
    }
  }
}

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  install(moduleObject.default)
  return moduleObject
})
