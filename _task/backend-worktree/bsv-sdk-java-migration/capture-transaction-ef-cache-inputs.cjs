// 固定 Transaction.ef-cache.test.ts 原输入：addInput/addOutput 实参、sign 与 EF 序列化结果。
// Transaction 与 Beef 互相引用，因此用真实模块只包装原型方法，避免 jest.doMock 的循环加载。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_TRANSACTION_EF_CACHE_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Transaction EF 缓存原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/Transaction.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false
let addInputOriginal, addOutputOriginal, toEFBinaryOriginal, toEFUint8ArrayOriginal, toEFOriginal, signOriginal

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/Transaction\.ef-cache\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('Transaction EF 缓存入口缺少固定原测试调用位置')
  return Number(match[1])
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('Transaction EF 缓存入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function observe (method, args, action, describe) {
  if (depth !== 0) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? result : describe(result))
    return result
  } finally {
    depth--
  }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function asm (script) { return script === null || script === undefined ? null : script.toASM() }
function jsNumber (value) {
  return Number.isInteger(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER ? value : String(value)
}
function describeInput (input) {
  return { sourceTXID: input.sourceTXID ?? null,
    sourceOutputIndex: jsNumber(input.sourceOutputIndex ?? 0),
    unlockingScript: asm(input.unlockingScript ?? null),
    hasTemplate: typeof input.unlockingScriptTemplate === 'object' && input.unlockingScriptTemplate !== null,
    hasSourceTransaction: typeof input.sourceTransaction === 'object' && input.sourceTransaction !== null }
}
function describeOutput (item) {
  return { satoshis: jsNumber(item.satoshis), lockingScript: asm(item.lockingScript) }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function install (Original) {
addInputOriginal = Original.prototype.addInput
addOutputOriginal = Original.prototype.addOutput
toEFBinaryOriginal = Original.prototype.toEFBinary
toEFUint8ArrayOriginal = Original.prototype.toEFUint8Array
toEFOriginal = Original.prototype.toEF
signOriginal = Original.prototype.sign
Original.prototype.addInput = function (...args) {
  return observe('addInput', [describeInput(args[0])], () => Reflect.apply(addInputOriginal, this, args), () => null)
}
Original.prototype.addOutput = function (...args) {
  return observe('addOutput', [describeOutput(args[0])], () => Reflect.apply(addOutputOriginal, this, args), () => null)
}
Original.prototype.toEFBinary = function (...args) {
  return observe('toEFBinary', [], () => Reflect.apply(toEFBinaryOriginal, this, args),
    result => ({ kind: 'bytes', hex: hex(result) }))
}
Original.prototype.toEFUint8Array = function (...args) {
  return observe('toEFUint8Array', [], () => Reflect.apply(toEFUint8ArrayOriginal, this, args),
    result => ({ kind: 'bytes', hex: hex(result) }))
}
Original.prototype.toEF = function (...args) {
  return observe('toEF', [], () => Reflect.apply(toEFOriginal, this, args),
    result => ({ kind: 'numberArray', hex: hex(Uint8Array.from(result)), length: result.length }))
}
Original.prototype.sign = async function (...args) {
  if (depth !== 0) return Reflect.apply(signOriginal, this, args)
  depth++
  try {
    const result = await Reflect.apply(signOriginal, this, args)
    record('sign', [], null)
    return result
  } finally {
    depth--
  }
}
}

// Transaction 与 Beef 互相引用：只包装原型方法，且只安装一次，避免工厂重入时拿到半初始化的模块。
jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  install(moduleObject.default)
  return moduleObject
})
