// 固定 BigNumber.additional.test.ts 原输入：词长上限、符号访问器、inspect、位数组、进制输出、
// 无符号位运算别名、移位与小数别名、fromBits/toBits、toSm、toRed。属性访问在原型访问器上包装。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_BIGNUMBER_ADDITIONAL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 BigNumber additional 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/primitives/BigNumber.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/BigNumber\.additional\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('BigNumber additional 入口发生在固定测试之外')
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
/** 描述实参时禁止把内部调用（如 String(bn) 触发的 toString）当成入口记录。 */
function quiet (action) {
  depth++
  try { return action() } finally { depth-- }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function jsNumber (value) {
  // JSON 无法表示 Infinity/NaN；其余 JS number（含小数）保持数值形态。
  return Number.isFinite(value) ? value : String(value)
}
function describeBigNumber (value) { return { kind: 'bigNumber', value: String(value) } }
function describeString (value) { return { kind: 'string', value } }
function describeNumberArray (values) {
  const bytes = Uint8Array.from(values, item => Number(item))
  return { kind: 'numberArray', hex: hex(bytes), length: values.length }
}
function describeWords (value) { return { kind: 'words', length: value.length } }
function describeReductionContext (value) { return { kind: 'reductionContext', m: String(value.m) } }

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function wrapAccessor (Original, property, getter, setter, describe) {
  const descriptor = Object.getOwnPropertyDescriptor(Original.prototype, property)
  if (!descriptor || typeof descriptor.get !== 'function') throw new Error('缺少原型访问器：' + property)
  const wrapped = { configurable: descriptor.configurable, enumerable: descriptor.enumerable,
    get: function (...values) {
      return observe(getter, [], () => Reflect.apply(descriptor.get, this, values), describe)
    } }
  if (descriptor.set) {
    wrapped.set = function (...values) {
      return observe(setter, [jsNumber(values[0])], () => Reflect.apply(descriptor.set, this, values))
    }
  }
  Object.defineProperty(Original.prototype, property, wrapped)
}

function install (Original) {
  const prototype = {}
  for (const method of ['expand', 'mul', 'inspect', 'toRed', 'toBitArray', 'toString', 'uor', 'uand', 'uxor',
    'iushln', 'addn', 'divn', '_iaddn', 'toNumber', 'ucmp', 'toBits', 'toSm']) {
    prototype[method] = Original.prototype[method]
  }
  // 实例 toBitArray 与静态同名但签名不同，必须分别保存原函数。
  const statics = {}
  for (const method of ['toBitArray', 'fromBits', 'fromHex']) statics[method] = Original[method]

  const wrap = (original, method, args, describe) => function (...values) {
    return observe(method, quiet(() => args(values)), () => Reflect.apply(original, this, values), describe)
  }
  Original.prototype.expand = wrap(prototype.expand, 'expand', values => values.map(jsNumber), describeBigNumber)
  Original.prototype.mul = wrap(prototype.mul, 'mul', values => [describeBigNumber(values[0])], describeBigNumber)
  Original.prototype.inspect = wrap(prototype.inspect, 'inspect', () => [], describeString)
  Original.prototype.toRed = wrap(prototype.toRed, 'toRed',
    values => [describeReductionContext(values[0])], describeBigNumber)
  Original.prototype.toBitArray = wrap(prototype.toBitArray, 'toBitArray', () => [], describeNumberArray)
  Original.prototype.toString = wrap(prototype.toString, 'toString', values => values.map(jsNumber), describeString)
  Original.prototype.uor = wrap(prototype.uor, 'uor', values => [describeBigNumber(values[0])], describeBigNumber)
  Original.prototype.uand = wrap(prototype.uand, 'uand', values => [describeBigNumber(values[0])], describeBigNumber)
  Original.prototype.uxor = wrap(prototype.uxor, 'uxor', values => [describeBigNumber(values[0])], describeBigNumber)
  Original.prototype.iushln = wrap(prototype.iushln, 'iushln', values => values.map(jsNumber), describeBigNumber)
  Original.prototype.addn = wrap(prototype.addn, 'addn', values => values.map(jsNumber), describeBigNumber)
  Original.prototype.divn = wrap(prototype.divn, 'divn', values => values.map(jsNumber), describeBigNumber)
  Original.prototype._iaddn = wrap(prototype._iaddn, '_iaddn', values => values.map(jsNumber), describeBigNumber)
  Original.prototype.toNumber = wrap(prototype.toNumber, 'toNumber', () => [], jsNumber)
  Original.prototype.ucmp = wrap(prototype.ucmp, 'ucmp', values => [describeBigNumber(values[0])], jsNumber)
  Original.prototype.toBits = wrap(prototype.toBits, 'toBits', () => [], jsNumber)
  Original.prototype.toSm = wrap(prototype.toSm, 'toSm', () => [], describeNumberArray)
  Original.toBitArray = wrap(statics.toBitArray, 'toBitArray',
    values => [describeBigNumber(values[0])], describeNumberArray)
  Original.fromBits = wrap(statics.fromBits, 'fromBits', values => values.map(jsNumber), describeBigNumber)
  Original.fromHex = wrap(statics.fromHex, 'fromHex', values => [values[0]], describeBigNumber)
  wrapAccessor(Original, 'negative', 'getNegative', 'setNegative', jsNumber)
  wrapAccessor(Original, 'words', 'getWords', 'setWords', describeWords)
}

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  install(moduleObject.default)
  return moduleObject
})
