// 固定 Curve.additional.test.ts：用真实模块只包装 Curve 的静态方法与原型方法。
// 只登记原测试直接发起的调用；Curve 内部（构造、惰性 endo 求值）触发的调用不算原入口。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_CURVE_ADDITIONAL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Curve.additional 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = 'src/primitives/__tests/Curve.additional.test.ts'
const curvePath = path.join(sdk, 'src/primitives/Curve.ts')
const probeName = 'capture-curve-additional-inputs.cjs'
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

function current () { return expect.getState().currentTestName }
/** 只登记本探针负责的原测试文件；同一次 Jest 运行里的其他原文件不属于本账本。 */
function mine () {
  const observed = expect.getState().testPath
  return typeof observed === 'string' && observed.endsWith('/' + sourceFile)
}
/** 只有原测试直接发起的调用才算入口：直接调用者的栈帧必须是本原文件。 */
function callerIsTest () {
  const stack = (new Error().stack || '').split('\n').slice(1)
  for (const line of stack) {
    if (line.includes(probeName)) continue
    if (line.includes('/node_modules/')) continue
    return line.includes(sourceFile)
  }
  return false
}
function callLine () {
  const match = (new Error().stack || '').match(/Curve\.additional\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test || !mine()) return false
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
  return true
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function observe (method, args, action, describe) {
  if (depth !== 0 || !callerIsTest()) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? { kind: 'undefined' } : describe(result))
    return result
  } catch (error) {
    record(method, args, thrown(error))
    throw error
  } finally {
    depth--
  }
}

function hexOf (value) {
  if (value === null || value === undefined) return null
  const plain = value.red ? value.fromRed() : value
  return plain.toString(16)
}
function bigNumber (value) { return { kind: 'bigNumber', value: hexOf(value) } }
function number (value) { return { kind: 'number', value: Number(value) } }
function boolean (value) { return { kind: 'boolean', value: Boolean(value) } }
function string (value) { return { kind: 'string', value: String(value) } }
function undefinedValue () { return { kind: 'undefined' } }
function numberArray (value) { return { kind: 'numberArray', value: Array.from(value, Number) } }
function numberArrays (value) { return { kind: 'array', value: Array.from(value, numberArray) } }
function point (value) {
  if (value === null || value === undefined) return { kind: 'null' }
  if (value.isInfinity()) return { kind: 'point', infinity: true }
  return { kind: 'point', infinity: false, x: hexOf(value.getX()), y: hexOf(value.getY()) }
}
function basisVector (value) { return { kind: 'basisVector', a: hexOf(value.a), b: hexOf(value.b) } }
function endoSplit (value) { return { kind: 'endoSplit', k1: hexOf(value.k1), k2: hexOf(value.k2) } }
function expression (value) {
  if (value === null || value === undefined) return { kind: 'null' }
  if (typeof value === 'boolean') return boolean(value)
  if (typeof value === 'number') return number(value)
  if (typeof value === 'string') return string(value)
  return bigNumber(value)
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(curvePath, () => {
  const moduleObject = jest.requireActual(curvePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  const Original = moduleObject.default
  const statics = {
    assert: Original.assert,
    parseBytes: Original.parseBytes,
    intFromLE: Original.intFromLE,
    cachedProperty: Original.cachedProperty
  }
  Original.assert = function (...args) {
    const list = [expression(args[0])]
    if (args.length > 1 && args[1] !== undefined) list.push(string(args[1]))
    return observe('assert', list, () => Reflect.apply(statics.assert, this, args), undefinedValue)
  }
  Original.parseBytes = function (...args) {
    const arg = typeof args[0] === 'string' ? string(args[0]) : numberArray(args[0])
    return observe('parseBytes', [arg], () => Reflect.apply(statics.parseBytes, this, args), numberArray)
  }
  Original.intFromLE = function (...args) {
    return observe('intFromLE', [numberArray(args[0])],
      () => Reflect.apply(statics.intFromLE, this, args), bigNumber)
  }
  Original.cachedProperty = function (...args) {
    if (depth !== 0 || !callerIsTest()) return Reflect.apply(statics.cachedProperty, this, args)
    depth++
    try {
      // 原测试只关心首次计算的结果与计算次数；把计算回调的调用单独登记为一条入口。
      const computer = args[2]
      const wrapped = function (...inner) {
        const value = Reflect.apply(computer, this, inner)
        record('cachedProperty.compute', [], number(value))
        return value
      }
      const result = Reflect.apply(statics.cachedProperty, this, [args[0], args[1], wrapped])
      record('cachedProperty', [string(args[1]), { kind: 'function' }],
        result === undefined ? undefinedValue() : number(result))
      return result
    } finally {
      depth--
    }
  }
  const prototype = Original.prototype
  const methods = {
    getNAF: prototype.getNAF,
    getJSF: prototype.getJSF,
    validate: prototype.validate,
    _endoSplit: prototype._endoSplit,
    _getEndoRoots: prototype._getEndoRoots,
    _getEndoBasis: prototype._getEndoBasis
  }
  prototype.getNAF = function (...args) {
    return observe('getNAF', [bigNumber(args[0]), number(args[1]), number(args[2])],
      () => Reflect.apply(methods.getNAF, this, args), numberArray)
  }
  prototype.getJSF = function (...args) {
    return observe('getJSF', [bigNumber(args[0]), bigNumber(args[1])],
      () => Reflect.apply(methods.getJSF, this, args), numberArrays)
  }
  prototype.validate = function (...args) {
    return observe('validate', [point(args[0])],
      () => Reflect.apply(methods.validate, this, args), boolean)
  }
  prototype._endoSplit = function (...args) {
    return observe('_endoSplit', [bigNumber(args[0])],
      () => Reflect.apply(methods._endoSplit, this, args), endoSplit)
  }
  prototype._getEndoRoots = function (...args) {
    return observe('_getEndoRoots', [bigNumber(args[0])],
      () => Reflect.apply(methods._getEndoRoots, this, args),
      value => ({ kind: 'array', value: Array.from(value, bigNumber) }))
  }
  prototype._getEndoBasis = function (...args) {
    return observe('_getEndoBasis', [bigNumber(args[0])],
      () => Reflect.apply(methods._getEndoBasis, this, args),
      value => ({ kind: 'array', value: Array.from(value, basisVector) }))
  }
  return moduleObject
})
