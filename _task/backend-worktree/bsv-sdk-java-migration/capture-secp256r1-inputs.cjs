// 固定 Secp256r1.test.ts：包装真实 Secp256r1 原型的公开入口，随机入口登记结果后由
// Java 侧用同一标量重放；其余入口都是确定性纯函数，逐值比较 x/y、hex、签名与布尔结果。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_SECP256R1_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Secp256r1 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = 'src/primitives/__tests/Secp256r1.test.ts'
const secp256r1Path = path.join(sdk, 'src/primitives/Secp256r1.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installedCurve = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/Secp256r1\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
/** 只登记本探针负责的原测试文件；同一次 Jest 运行里的其他原文件不属于本账本。 */
function mine () {
  const observed = expect.getState().testPath
  return typeof observed === 'string' && observed.endsWith('/' + sourceFile)
}
/** 模块加载期的固定调用不属于任何原用例，不进入账本。 */
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

// —— 描述：坐标、编码、签名与字节都取两侧可复现的表示 ——
function scalar (value) { return { kind: 'string', value: String(value) } }
function pointArg (value) {
  if (value == null) return null
  // 原测试会把无效公钥字符串直接交给 verify；此时 Point 的 x/y 是 undefined，
  // Java 侧同样以 undefined 记录该分支，两侧形状保持一致。
  return { x: { kind: 'string', value: value.x === undefined ? 'undefined' : String(value.x) },
    y: { kind: 'string', value: value.y === undefined ? 'undefined' : String(value.y) } }
}
function pointResult (value) {
  if (value == null) return null
  return { kind: 'point', x: String(value.x), y: String(value.y) }
}
function signature (value) { return { kind: 'signature', r: String(value.r), s: String(value.s) } }
function bytes (value) { return { kind: 'array', value: Array.from(value, item => ({ type: 'number', value: String(item) })) } }
function hex (value) { return { kind: 'string', value: String(value) } }
function boolean (value) { return { kind: 'boolean', value: Boolean(value) } }
function options (value) {
  return { prehashed: value !== undefined && value.prehashed === true,
    nonce: value !== undefined && value.nonce !== undefined ? String(value.nonce) : null }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(secp256r1Path, () => {
  const moduleObject = jest.requireActual(secp256r1Path)
  if (installedCurve || moduleObject.default === undefined) return moduleObject
  installedCurve = true
  const Original = moduleObject.default
  /** 只包一次，避免 mock 工厂重复求值时叠加包装。 */
  function wrap (name, factory) {
    const original = Original.prototype[name]
    if (typeof original !== 'function' || original.__probeWrapped === true) return
    const wrapped = factory(original)
    wrapped.__probeWrapped = true
    Object.defineProperty(Original.prototype, name, { value: wrapped, writable: true, configurable: true })
  }
  // 随机入口：结果就是原测试实际使用的私钥标量，Java 侧据此重放同一入口。
  wrap('generatePrivateKeyHex', original => function (...args) {
    return observe('generatePrivateKeyHex', [], () => Reflect.apply(original, this, args), hex)
  })
  wrap('multiplyBase', original => function (...args) {
    return observe('multiplyBase', [scalar(args[0])], () => Reflect.apply(original, this, args), pointResult)
  })
  wrap('multiply', original => function (...args) {
    return observe('multiply', [pointArg(args[0]), scalar(args[1])], () => Reflect.apply(original, this, args), pointResult)
  })
  wrap('pointToHex', original => function (...args) {
    return observe('pointToHex', [pointArg(args[0]), boolean(args.length > 1 ? args[1] : false)],
      () => Reflect.apply(original, this, args), hex)
  })
  wrap('pointFromHex', original => function (...args) {
    return observe('pointFromHex', [scalar(args[0])], () => Reflect.apply(original, this, args), pointResult)
  })
  wrap('add', original => function (...args) {
    return observe('add', [pointArg(args[0]), pointArg(args[1])], () => Reflect.apply(original, this, args), pointResult)
  })
  wrap('isOnCurve', original => function (...args) {
    return observe('isOnCurve', [pointArg(args[0])], () => Reflect.apply(original, this, args), boolean)
  })
  wrap('publicKeyFromPrivate', original => function (...args) {
    return observe('publicKeyFromPrivate', [scalar(args[0])], () => Reflect.apply(original, this, args), pointResult)
  })
  wrap('sign', original => function (...args) {
    return observe('sign', [bytes(args[0]), scalar(args[1]), options(args[2])],
      () => Reflect.apply(original, this, args), signature)
  })
  wrap('verify', original => function (...args) {
    return observe('verify',
      [bytes(args[0]), signature(args[1]), pointArg(args[2]), boolean(args.length > 3 ? args[3] : false)],
      () => Reflect.apply(original, this, args), boolean)
  })
  return moduleObject
})
