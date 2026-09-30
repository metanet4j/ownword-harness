// 固定 Schnorr.test.ts：记录原测试直接发起的随机私钥与 Schnorr 证明入口。
// 证明里的一次性随机私钥由 Schnorr.generateProof 内部产生，因此 fromRandom 不参与深度守卫；
// 其余入口只在最外层调用（立即调用者是原测试）时登记。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_SCHNORR_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Schnorr 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
// 探针作为 setup 文件会在同一次运行的每个原文件环境里各加载一次；
// 只有本探测负责的原文件才登记入口，其余环境只放行不记录。
const sourceFile = 'src/primitives/__tests/Schnorr.test.ts'
const schnorrPath = path.join(sdk, 'src/primitives/Schnorr.ts')
const privateKeyPath = path.join(sdk, 'src/primitives/PrivateKey.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installedSchnorr = false
let installedPrivateKey = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/Schnorr\.test\.ts:(\d+):\d+/)
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

function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function privateKey (value) { return { kind: 'privateKey', hex: hex(value.toArray('be', 32)) } }
function point (value) {
  if (value === null || value === undefined) return { kind: 'null' }
  if (value.isInfinity()) return { kind: 'point', infinity: true }
  return { kind: 'point', x: String(value.getX()), y: String(value.getY()) }
}
function proof (value) {
  if (value === null || value === undefined) return { kind: 'null' }
  return { kind: 'proof', R: point(value.R), SPrime: point(value.SPrime), z: String(value.z) }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(privateKeyPath, () => {
  const moduleObject = jest.requireActual(privateKeyPath)
  if (installedPrivateKey || moduleObject.default === undefined) return moduleObject
  installedPrivateKey = true
  const Original = moduleObject.default
  const originalFromRandom = Original.fromRandom
  Original.fromRandom = function (...args) {
    const key = Reflect.apply(originalFromRandom, this, args)
    record('fromRandom', [], privateKey(key))
    return key
  }
  return moduleObject
})

jest.doMock(schnorrPath, () => {
  const moduleObject = jest.requireActual(schnorrPath)
  if (installedSchnorr || moduleObject.default === undefined) return moduleObject
  installedSchnorr = true
  const Original = moduleObject.default
  const originalGenerate = Original.prototype.generateProof
  const originalVerify = Original.prototype.verifyProof
  Original.prototype.generateProof = function (...args) {
    return observe('generateProof',
      [privateKey(args[0]), point(args[1]), point(args[2]), point(args[3])],
      () => Reflect.apply(originalGenerate, this, args), proof)
  }
  Original.prototype.verifyProof = function (...args) {
    return observe('verifyProof',
      [point(args[0]), point(args[1]), point(args[2]), proof(args[3])],
      () => Reflect.apply(originalVerify, this, args), value => ({ kind: 'boolean', value }))
  }
  return moduleObject
})
