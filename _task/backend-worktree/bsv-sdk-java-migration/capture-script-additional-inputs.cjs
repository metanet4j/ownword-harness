// 固定 Script.additional.test.ts 原输入：Script 的解析入口与写块/改写/查找删除入口。
// 用真实模块只包装原型与静态方法，避免 jest.doMock 改变类的身份（断言里要比较 Script 实例）。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_SCRIPT_ADDITIONAL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Script additional 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/script/Script.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  // 行号只作说明，样本身份用入口名与序号。
  const match = new Error().stack.match(/Script\.additional\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('Script additional 入口发生在固定测试之外')
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
function describeNumberArray (values) {
  return { kind: 'numberArray', hex: hex(Uint8Array.from(values)), length: values.length }
}
function describeBigNumber (value) { return { kind: 'bigNumber', value: String(value) } }
function describeString (value) { return { kind: 'string', value } }
function describeBoolean (value) { return { kind: 'boolean', value } }
function plain (value) { return typeof value === 'number' ? value : String(value) }

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function install (Original) {
  const originals = {}
  for (const method of ['toASM', 'writeScript', 'setChunkOpCode', 'writeBn', 'writeNumber', 'writeBin',
    'writeOpCode', 'findAndDelete', 'isLockingScript', 'isUnlockingScript']) {
    originals[method] = Original.prototype[method]
  }
  originals.fromHex = Original.fromHex
  originals.fromASM = Original.fromASM

  Original.fromHex = function (...values) {
    return observe('fromHex', [values[0]], () => Reflect.apply(originals.fromHex, this, values), describeScript)
  }
  Original.fromASM = function (...values) {
    return observe('fromASM', [values[0]], () => Reflect.apply(originals.fromASM, this, values), describeScript)
  }
  Original.prototype.toASM = function (...values) {
    return observe('toASM', [], () => Reflect.apply(originals.toASM, this, values), describeString)
  }
  Original.prototype.writeScript = function (...values) {
    return observe('writeScript', [describeScript(values[0])],
      () => Reflect.apply(originals.writeScript, this, values), describeScript)
  }
  Original.prototype.setChunkOpCode = function (...values) {
    return observe('setChunkOpCode', values.map(plain),
      () => Reflect.apply(originals.setChunkOpCode, this, values), describeScript)
  }
  Original.prototype.writeBn = function (...values) {
    return observe('writeBn', [describeBigNumber(values[0])],
      () => Reflect.apply(originals.writeBn, this, values), describeScript)
  }
  Original.prototype.writeNumber = function (...values) {
    return observe('writeNumber', values.map(plain),
      () => Reflect.apply(originals.writeNumber, this, values), describeScript)
  }
  Original.prototype.writeBin = function (...values) {
    return observe('writeBin', [describeNumberArray(values[0])],
      () => Reflect.apply(originals.writeBin, this, values), describeScript)
  }
  Original.prototype.writeOpCode = function (...values) {
    return observe('writeOpCode', values.map(plain),
      () => Reflect.apply(originals.writeOpCode, this, values), describeScript)
  }
  Original.prototype.findAndDelete = function (...values) {
    return observe('findAndDelete', [describeScript(values[0])],
      () => Reflect.apply(originals.findAndDelete, this, values), describeScript)
  }
  Original.prototype.isLockingScript = function (...values) {
    return observe('isLockingScript', [], () => Reflect.apply(originals.isLockingScript, this, values), describeBoolean)
  }
  Original.prototype.isUnlockingScript = function (...values) {
    return observe('isUnlockingScript', [], () => Reflect.apply(originals.isUnlockingScript, this, values), describeBoolean)
  }
}

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  install(moduleObject.default)
  return moduleObject
})
