// 固定 Curve.unit.test.ts：用真实模块只包装 Curve／Point／JacobianPoint 的原型与静态方法。
// 只登记原测试直接发起的调用；曲线点结果按仿射坐标逐值比较，内部计算不计入口。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_CURVE_UNIT_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Curve.unit 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = 'src/primitives/__tests/Curve.unit.test.ts'
const probeName = 'capture-curve-unit-inputs.cjs'
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
  const match = (new Error().stack || '').match(/Curve\.unit\.test\.ts:(\d+):\d+/)
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
    record(method, args, describe === undefined ? undefinedValue() : describe(result))
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
function objectValue (value) {
  return { kind: 'object', keys: Object.keys(value).sort() }
}
function scalar (value) {
  if (value === null || value === undefined) return { kind: 'undefined' }
  if (typeof value === 'string') return string(value)
  if (typeof value === 'number') return number(value)
  return bigNumber(value)
}
function point (value) {
  if (value === null || value === undefined) return { kind: 'null' }
  if (value.isInfinity()) return { kind: 'point', infinity: true }
  return { kind: 'point', infinity: false, x: hexOf(value.getX()), y: hexOf(value.getY()) }
}
/** JPoint 统一按仿射点比较：坐标相同即同一个点，与内部 Jacobian 表示无关。 */
function jacobian (value) { return point(value.toP()) }
function basisVector (value) { return { kind: 'basisVector', a: hexOf(value.a), b: hexOf(value.b) } }
function endoSplit (value) { return { kind: 'endoSplit', k1: hexOf(value.k1), k2: hexOf(value.k2) } }
function endomorphism (value) {
  return { kind: 'endomorphism', beta: hexOf(value.beta.fromRed()), lambda: hexOf(value.lambda),
    basis: Array.from(value.basis, basisVector) }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(path.join(sdk, 'src/primitives/Curve.ts'), () => {
  const curvePath = path.join(sdk, 'src/primitives/Curve.ts')
  const pointPath = path.join(sdk, 'src/primitives/Point.ts')
  const jacobianPath = path.join(sdk, 'src/primitives/JacobianPoint.ts')
  const moduleObject = jest.requireActual(curvePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true

  function wrap (Type, name, describe) {
    const original = Object.getOwnPropertyDescriptor(Type.prototype, name)
    if (original === undefined || typeof original.value !== 'function') {
      throw new Error('缺少原方法：' + Type.name + '.' + name)
    }
    Object.defineProperty(Type.prototype, name, { ...original, value: function (...args) {
      return observe(Type.name + '.' + name, args.map(argument), () => Reflect.apply(original.value, this, args),
        value => describe(value))
    } })
  }
  function wrapStatic (Type, name, describe) {
    const original = Type[name]
    if (typeof original !== 'function') throw new Error('缺少原静态方法：' + Type.name + '.' + name)
    Type[name] = function (...args) {
      return observe(Type.name + '.' + name, args.map(argument), () => Reflect.apply(original, Type, args),
        value => describe(value))
    }
  }
  function argument (value) {
    if (value === null || value === undefined) return { kind: 'undefined' }
    if (typeof value === 'boolean') return boolean(value)
    if (typeof value === 'number') return number(value)
    if (typeof value === 'string') return string(value)
    if (PointType && value instanceof PointType) return point(value)
    if (JPointType && value instanceof JPointType) return jacobian(value)
    if (Object.getPrototypeOf(value) === Object.prototype) return objectValue(value)
    return bigNumber(value)
  }

  const PointType = jest.requireActual(pointPath).default
  const JPointType = jest.requireActual(jacobianPath).default

  // Curve：原测试只直接调用这几个私有入口。
  wrap(moduleObject.default, '_endoSplit', endoSplit)
  wrap(moduleObject.default, '_getEndomorphism', endomorphism)
  wrap(moduleObject.default, '_endomorphismLambdaMatches', boolean)
  wrap(moduleObject.default, '_resolveEndomorphismBeta', bigNumber)
  wrap(moduleObject.default, '_resolveEndomorphismLambda', bigNumber)

  // Point：曲线点运算逐个比值。
  wrap(PointType, 'validate', boolean)
  wrap(PointType, 'dbl', point)
  wrap(PointType, 'add', point)
  wrap(PointType, 'mul', point)
  wrap(PointType, 'toJ', jacobian)
  wrap(PointType, 'eq', boolean)
  wrap(PointType, 'encode', string)
  wrapStatic(PointType, 'fromString', point)

  // JacobianPoint：无穷远与相等语义按仿射点比较。
  wrap(JPointType, 'isInfinity', boolean)
  wrap(JPointType, 'eq', boolean)
  wrap(JPointType, 'add', jacobian)
  wrap(JPointType, 'neg', jacobian)
  wrap(JPointType, 'dbl', jacobian)
  wrap(JPointType, 'toP', point)

  return moduleObject
})
