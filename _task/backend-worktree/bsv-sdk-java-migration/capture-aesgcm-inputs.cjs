// 固定 AESGCM.test.ts 原输入：AES/GCM 原语工具函数的实际实参与返回结果。
// AESGCM.ts 只有具名导出，因此用 jest.doMock 包装导出函数，内部调用仍走模块本地绑定。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_AESGCM_TS_OBSERVATIONS
if (!output) throw new Error('缺少 AESGCM 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/primitives/AESGCM.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/AESGCM\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('AESGCM 入口发生在固定测试之外')
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
function bytes (value) { return { kind: 'bytes', hex: hex(Uint8Array.from(value)) } }
function jsNumber (value) {
  return Number.isInteger(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER ? value : String(value)
}
function describeBytesArgs (values) { return values.map(bytes) }
function number (value) { return { kind: 'number', value: jsNumber(value) } }
function describeResult (value) {
  return { kind: 'result', result: bytes(value.result), authenticationTag: bytes(value.authenticationTag) }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function install (moduleObject) {
  const originals = {}
  for (const method of ['AES', 'ghash', 'AESGCM', 'AESGCMDecrypt', 'exclusiveOR', 'rightShift',
    'multiply', 'incrementLeastSignificantThirtyTwoBits', 'checkBit', 'getBytes']) {
    originals[method] = moduleObject[method]
  }
  moduleObject.AES = function (...args) {
    return observe('AES', describeBytesArgs(args), () => Reflect.apply(originals.AES, this, args), bytes)
  }
  moduleObject.ghash = function (...args) {
    return observe('ghash', describeBytesArgs(args), () => Reflect.apply(originals.ghash, this, args), bytes)
  }
  moduleObject.AESGCM = function (...args) {
    return observe('AESGCM', describeBytesArgs(args), () => Reflect.apply(originals.AESGCM, this, args), describeResult)
  }
  moduleObject.AESGCMDecrypt = function (...args) {
    return observe('AESGCMDecrypt', describeBytesArgs(args), () => Reflect.apply(originals.AESGCMDecrypt, this, args), bytes)
  }
  moduleObject.exclusiveOR = function (...args) {
    return observe('exclusiveOR', describeBytesArgs(args), () => Reflect.apply(originals.exclusiveOR, this, args), bytes)
  }
  moduleObject.rightShift = function (...args) {
    return observe('rightShift', describeBytesArgs(args), () => Reflect.apply(originals.rightShift, this, args), bytes)
  }
  moduleObject.multiply = function (...args) {
    return observe('multiply', describeBytesArgs(args), () => Reflect.apply(originals.multiply, this, args), bytes)
  }
  moduleObject.incrementLeastSignificantThirtyTwoBits = function (...args) {
    return observe('incrementLeastSignificantThirtyTwoBits', describeBytesArgs(args),
      () => Reflect.apply(originals.incrementLeastSignificantThirtyTwoBits, this, args), bytes)
  }
  moduleObject.checkBit = function (...args) {
    return observe('checkBit', [bytes(args[0]), number(args[1]), number(args[2])],
      () => Reflect.apply(originals.checkBit, this, args), result => number(result))
  }
  moduleObject.getBytes = function (...args) {
    return observe('getBytes', [number(args[0])], () => Reflect.apply(originals.getBytes, this, args), bytes)
  }
}

// 只包装一次并返回同一模块对象，避免 jest 工厂重入时拿到半包装的导出。
jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.AES === undefined) return moduleObject
  installed = true
  install(moduleObject)
  return moduleObject
})
