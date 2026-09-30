// 固定 Script.test.ts 除 1030 条向量以外的 39 个原用例输入：解析入口（fromHex／fromBinary／
// fromASM）、ASM/hex 输出、写入与查找入口。Script 会与模板互相引用，因此用真实模块只包装
// 原型与静态方法；fromAddress 用例的熵来自 Java 侧同一份固定私钥，两端消费同一把密钥。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_SCRIPT_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Script 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/script/Script.ts')
// 原文件的 1030 条向量归 ScriptVectorsTest（另一局部）；本探针只登记 ScriptTest 的 39 个用例。
const catalog = JSON.parse(fs.readFileSync(path.join(__dirname, 'module-tests.json'), 'utf8'))
const mapping = JSON.parse(fs.readFileSync(path.join(__dirname, 'test-map.json'), 'utf8'))
const source = catalog.files.find(item => item.path === sourceFile)
if (source === undefined) throw new Error('固定 Script 原文件未登记：' + sourceFile)
const owned = new Set(mapping.cases
  .filter(item => item.java.length === 1 && item.java[0].className === 'com.metanet4j.bsv.script.ScriptTest')
  .map(item => item.id))
const localTests = new Set(source.cases.filter(item => owned.has(item.id)).map(item => item.names.join(' ')))
if (localTests.size !== 39) throw new Error('固定 ScriptTest 用例清单不符：' + localTests.size)
const occurrences = new Map()
const entryCounts = new Map()
let activeTest = null
let activeOccurrence = 0
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

// 原测试用 PrivateKey.fromRandom() 生成三个地址；按 Java 侧固定私钥播种熵流，
// 让两侧的 address／pkh／ASM 逐值可比（顺序与 ScriptTest 的 address0..2 一致）。
const originalCrypto = globalThis.crypto
const ENTROPY = (() => {
  const file = path.join(__dirname, 'metanet4j-bsv-sdk/src/test/resources/script-model-random.properties')
  const text = fs.readFileSync(file, 'utf8')
  return ['address0', 'address1', 'address2'].map(name => {
    const line = text.split('\n').find(item => item.startsWith(name + '='))
    if (line === undefined) throw new Error('缺少固定 Script 随机私钥：' + name)
    return Buffer.from(line.slice(name.length + 1).trim(), 'hex')
  })
})()
let entropyIndex = 0
Object.defineProperty(globalThis, 'crypto', {
  configurable: true,
  value: { subtle: originalCrypto?.subtle, getRandomValues (array) {
    if (entropyIndex >= ENTROPY.length) throw new Error('固定 Script 随机私钥不足，出现计划外的随机消费')
    const seed = ENTROPY[entropyIndex++]
    for (let index = 0; index < array.length; index++) array[index] = seed[index % seed.length]
    return array
  } }
})

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/Script\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, test = activeTest, at = activeOccurrence, line = callLine()) {
  if (!test || !localTests.has(test)) return
  const key = `${test}\0${at}`
  entryCounts.set(key, (entryCounts.get(key) || 0) + 1)
  fs.appendFileSync(output, JSON.stringify({ test, occurrence: at, sequence: ++sequence,
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
  let values = null
  try {
    // 入口实参的表征可能自己调用被包装的方法（如 findAndDelete 的 Script 目标），
    // 必须在同一层深度内完成，否则会多记内部调用。
    values = typeof args === 'function' ? args() : args
    const result = action()
    record(method, values, describe === undefined ? null : describe(result))
    return result
  } catch (error) {
    record(method, values, thrown(error))
    throw error
  } finally {
    depth--
  }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function jsNumber (value) {
  return Number.isInteger(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER ? value : String(value)
}
function describeNumberArray (values) {
  return { kind: 'numberArray', hex: hex(Uint8Array.from(values)), length: values.length }
}
function describeText (value) { return { kind: 'string', value } }
function describeNumber (value) { return { kind: 'number', value: jsNumber(value) } }
function describeBoolean (value) { return { kind: 'boolean', value } }
function describeScript (script) {
  if (script === null || script === undefined) return null
  return { kind: 'script', asm: script.toASM(), hex: script.toHex() }
}

beforeEach(() => {
  activeTest = current()
  occurrence = (occurrences.get(activeTest) || 0) + 1
  occurrences.set(activeTest, occurrence)
  activeOccurrence = occurrence
  sequence = 0
})

afterEach(() => {
  // fromAddress 的未知前缀用例在 P2PKH.lock 内部抛错，没有任何 Script 公开入口；
  // 用固定标记登记，Java 侧在对应位置发出同一条目，两侧仍然逐样本对齐。
  if (activeTest && !entryCounts.has(`${activeTest}\0${activeOccurrence}`)) {
    record('noEntryPoint', [], null, activeTest, activeOccurrence, null)
  }
  activeTest = null
  activeOccurrence = 0
})

function install (Original) {
  const statics = {}
  for (const method of ['fromHex', 'fromBinary', 'fromASM']) statics[method] = Original[method]
  const methods = {}
  for (const method of ['toASM', 'toHex', 'writeBin', 'writeOpCode', 'removeCodeseparators',
    'isPushOnly', 'findAndDelete']) methods[method] = Original.prototype[method]

  Original.fromHex = function (...args) {
    return observe('fromHex', [describeText(args[0])],
      () => Reflect.apply(statics.fromHex, this, args), describeScript)
  }
  Original.fromBinary = function (...args) {
    return observe('fromBinary', [describeNumberArray(args[0])],
      () => Reflect.apply(statics.fromBinary, this, args), describeScript)
  }
  Original.fromASM = function (...args) {
    return observe('fromASM', [describeText(args[0])],
      () => Reflect.apply(statics.fromASM, this, args), describeScript)
  }
  Original.prototype.toASM = function (...args) {
    return observe('toASM', [], () => Reflect.apply(methods.toASM, this, args), describeText)
  }
  Original.prototype.toHex = function (...args) {
    return observe('toHex', [], () => Reflect.apply(methods.toHex, this, args), describeText)
  }
  Original.prototype.writeBin = function (...args) {
    return observe('writeBin', [describeNumberArray(args[0])],
      () => Reflect.apply(methods.writeBin, this, args), undefined)
  }
  Original.prototype.writeOpCode = function (...args) {
    return observe('writeOpCode', [describeNumber(args[0])],
      () => Reflect.apply(methods.writeOpCode, this, args), undefined)
  }
  Original.prototype.removeCodeseparators = function (...args) {
    return observe('removeCodeseparators', [], () => Reflect.apply(methods.removeCodeseparators, this, args), undefined)
  }
  Original.prototype.isPushOnly = function (...args) {
    return observe('isPushOnly', [], () => Reflect.apply(methods.isPushOnly, this, args), describeBoolean)
  }
  Original.prototype.findAndDelete = function (...args) {
    return observe('findAndDelete', () => [describeScript(args[0])],
      () => Reflect.apply(methods.findAndDelete, this, args), undefined)
  }
}

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  install(moduleObject.default)
  return moduleObject
})
