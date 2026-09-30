// 固定 Hash.test.ts 原输入：四个哈希实现的 update／digest／digestHex／_pad 入口、模块级
// sha256／pbkdf2 与 TOB-20 字节序辅助函数。Hash 没有循环依赖，因此用真实模块只包装
// 原型方法与导出函数；未触达任何公开入口的用例（纯 JS 表达式）由 noEntryPoint 标记登记。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_HASH_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Hash 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/primitives/Hash.ts')
const occurrences = new Map()
const entryCounts = new Map()
let activeTest = null
let activeOccurrence = 0
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/Hash\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, test = activeTest, at = activeOccurrence, line = callLine()) {
  if (!test) return
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
function describeBytes (value) { return { kind: 'bytes', hex: hex(value) } }
function describeNumberArray (value) {
  return { kind: 'numberArray', hex: hex(Uint8Array.from(value)), length: value.length }
}
function describeMessage (value) {
  if (value === undefined) return { kind: 'undefined' }
  return Array.isArray(value) || value instanceof Uint8Array
    ? describeNumberArray(value) : { kind: 'string', value: String(value) }
}
function describeEncoding (value) { return value === undefined ? { kind: 'undefined' } : { kind: 'string', value } }
function describeNumber (value) { return { kind: 'number', value: jsNumber(value) } }
function describeText (value) { return { kind: 'string', value } }

beforeEach(() => {
  activeTest = current()
  occurrence = (occurrences.get(activeTest) || 0) + 1
  occurrences.set(activeTest, occurrence)
  activeOccurrence = occurrence
  sequence = 0
})

afterEach(() => {
  // 少数用例只做纯 JS 表达式（例如强制大端分支的本地箭头函数），没有 SDK 公开入口；
  // 用固定标记登记，Java 侧在对应位置发出同一条目，两侧仍然逐样本对齐。
  if (activeTest && !entryCounts.has(`${activeTest}\0${activeOccurrence}`)) {
    record('noEntryPoint', [], null, activeTest, activeOccurrence, null)
  }
  activeTest = null
  activeOccurrence = 0
})

function wrapPrototype (proto, method) {
  const original = proto[method]
  if (typeof original !== 'function') return
  proto[method] = function (...values) {
    const args = method === 'update'
      ? [describeMessage(values[0]), describeEncoding(values[1])] : []
    return observe(method, args, () => Reflect.apply(original, this, values),
      method === 'digestHex' ? describeText : method === 'update' ? undefined : describeNumberArray)
  }
}

function install (actual, original) {
  const base = Object.getPrototypeOf(original.SHA1.prototype)
  const prototypes = [...['SHA256', 'SHA1', 'SHA512', 'RIPEMD160'].map(className => {
    const klass = original[className]
    if (typeof klass !== 'function') throw new Error('Hash 导出类缺失：' + className)
    return klass.prototype
  }), base]
  for (const proto of prototypes) {
    for (const method of ['update', 'digest', 'digestHex', '_pad']) wrapPrototype(proto, method)
  }
  for (const name of ['sha256', 'pbkdf2', 'htonl', 'swapBytes32', 'realHtonl']) {
    if (typeof original[name] !== 'function') throw new Error('Hash 导出函数缺失：' + name)
  }
  actual.sha256 = function (...values) {
    return observe('sha256', [describeMessage(values[0]), describeEncoding(values[1])],
      () => Reflect.apply(original.sha256, this, values), describeNumberArray)
  }
  actual.pbkdf2 = function (...values) {
    return observe('pbkdf2', [describeBytes(values[0]), describeBytes(values[1]),
      describeNumber(values[2]), describeNumber(values[3])],
    () => Reflect.apply(original.pbkdf2, this, values), describeNumberArray)
  }
  for (const name of ['htonl', 'swapBytes32', 'realHtonl']) {
    actual[name] = function (...values) {
      return observe(name, [describeNumber(values[0])],
        () => Reflect.apply(original[name], this, values), describeNumber)
    }
  }
}

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed) return moduleObject
  installed = true
  const wrapped = { ...moduleObject }
  install(wrapped, moduleObject)
  return wrapped
})
