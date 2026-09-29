// 固定 LockingUnlockingScript.test.ts 原输入：两个 Script 子类的构造事件、继承自 Script 的 fromHex/toHex
// 以及各自的 isLockingScript/isUnlockingScript。类之间互相引用，因此用真实模块只包装原型/静态方法；
// 只 new、不调方法的用例（extends Script 类断言）靠构造函数 Proxy 记录 constructor 事件。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_LOCKING_UNLOCKING_SCRIPT_TS_OBSERVATIONS
if (!output) throw new Error('缺少 LockingUnlockingScript 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const scriptPath = path.join(sdk, 'src/script/Script.ts')
const lockingPath = path.join(sdk, 'src/script/LockingScript.ts')
const unlockingPath = path.join(sdk, 'src/script/UnlockingScript.ts')
const occurrences = new Map()
const installed = new Set()
let occurrence = 0
let sequence = 0
let depth = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  // 行号只作说明，样本身份用入口名与序号。
  const match = new Error().stack.match(/LockingUnlockingScript\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('LockingUnlockingScript 入口发生在固定测试之外')
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
function describeChunk (chunk) {
  const data = chunk.data === undefined || chunk.data === null ? null : hex(Uint8Array.from(chunk.data))
  return { op: chunk.op, data }
}
function describeScript (script) {
  if (script === null || script === undefined) return null
  return { kind: 'script', class: script.constructor.name, chunks: script.chunks.map(describeChunk),
    hex: script.toHex() }
}
function flag (value) { return { kind: 'boolean', value } }
function text (value) { return { kind: 'string', value } }

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function wrapConstructor (moduleObject) {
  const Original = moduleObject.default
  for (const [method, describe] of [['isLockingScript', flag], ['isUnlockingScript', flag]]) {
    const original = Original.prototype[method]
    Original.prototype[method] = function (...values) {
      return observe(method, [], () => Reflect.apply(original, this, values), describe)
    }
  }
  moduleObject.default = new Proxy(Original, {
    construct (target, args, newTarget) {
      return observe('constructor', [], () => Reflect.construct(target, args, newTarget), describeScript)
    }
  })
  return moduleObject
}

function wrapScript (moduleObject) {
  const Original = moduleObject.default
  const fromHex = Original.fromHex
  Original.fromHex = function (...values) {
    return observe('fromHex', [values[0]], () => Reflect.apply(fromHex, this, values), describeScript)
  }
  const toHex = Original.prototype.toHex
  Original.prototype.toHex = function (...values) {
    return observe('toHex', [], () => Reflect.apply(toHex, this, values), text)
  }
  return moduleObject
}

jest.doMock(scriptPath, () => {
  const moduleObject = jest.requireActual(scriptPath)
  if (installed.has(scriptPath) || moduleObject.default === undefined) return moduleObject
  installed.add(scriptPath)
  return wrapScript(moduleObject)
})

jest.doMock(lockingPath, () => {
  const moduleObject = jest.requireActual(lockingPath)
  if (installed.has(lockingPath) || moduleObject.default === undefined) return moduleObject
  installed.add(lockingPath)
  return wrapConstructor(moduleObject)
})

jest.doMock(unlockingPath, () => {
  const moduleObject = jest.requireActual(unlockingPath)
  if (installed.has(unlockingPath) || moduleObject.default === undefined) return moduleObject
  installed.add(unlockingPath)
  return wrapConstructor(moduleObject)
})
