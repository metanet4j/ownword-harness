// 固定 ECDSA.additional.test.ts：只记录原测试直接发起的 ECDSA 公开入口。
// ECDSA 是命名空间导入且与 Point／Signature 互相引用，因此用真实模块、只包装模块导出。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_ECDSA_ADDITIONAL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 ECDSA.additional 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
// 探针作为 setup 文件会在同一次运行的每个原文件环境里各加载一次；
// 只有本探测负责的原文件才登记入口，其余环境只放行不记录。
const sourceFile = 'src/primitives/__tests/ECDSA.additional.test.ts'
const ecdsaPath = path.join(sdk, 'src/primitives/ECDSA.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/ECDSA\.additional\.test\.ts:(\d+):\d+/)
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

function bigNumber (value) { return { kind: 'bigNumber', value: String(value) } }
function boolean (value) { return { kind: 'boolean', value: Boolean(value) } }
function point (value) {
  if (value == null) return null
  if (value.x == null || value.y == null) return { kind: 'point', x: null, y: null }
  return { kind: 'point', x: String(value.x), y: String(value.y) }
}
function signature (value) { return { kind: 'signature', r: String(value.r), s: String(value.s) } }
// customK 可以是固定标量或函数；函数的实际名字不参与比较，只登记下游真正可复现的入参。
function signArgs (args) {
  const list = [bigNumber(args[0]), bigNumber(args[1]), boolean(args[2])]
  const customK = args[3]
  if (typeof customK === 'function') return list
  if (customK !== undefined && customK !== null) list.push(bigNumber(customK))
  return list
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(ecdsaPath, () => {
  const moduleObject = jest.requireActual(ecdsaPath)
  // ECDSA 是命名空间导入：导出按属性读取；ECDSA 与 Signature／Point 互相引用，
  // 构造 mock 时命名导出可能尚未填充，因此原函数必须在调用时再解析。
  // ESM 实时绑定下工厂可能被求值多次，这里只在未包装过的导出上登记，避免叠加。
  // 原函数在包装时立刻解析并保存在闭包里：包装后模块导出已指向包装器，
  // 再按名字查一次会递归调用自己。
  function patch (name, factory) {
    const current = moduleObject[name]
    if (typeof current !== 'function' || current.__probeWrapped === true) return
    const wrapped = factory(current)
    wrapped.__probeWrapped = true
    Object.defineProperty(moduleObject, name, {
      value: wrapped, writable: true, configurable: true, enumerable: true
    })
  }
  patch('sign', original => function (...args) {
    return observe('sign', signArgs(args), () => Reflect.apply(original, this, args), signature)
  })
  patch('verify', original => function (...args) {
    return observe('verify',
      [bigNumber(args[0]), signature(args[1]), point(args[2])],
      () => Reflect.apply(original, this, args), value => ({ kind: 'boolean', value }))
  })
  return moduleObject
})
