// 固定 AsyncCryptoBackend.test.ts 原输入：可选异步后端注册／就绪查询／摘要校验的实际实参
// 与返回结果，以及后端桩在每次入口前的可观察状态（isReady／preload 次数／supportsCrypto）。
//
// 取值口径与原观察形状一致：`readyAsyncCryptoBackend` 未命中时 TS 返回 `undefined`，
// 命中的是注册的同一个后端实例。Java 侧据此重建同一个桩后端并按同一顺序消费样本。
// audit-tests.py 的固定语义规则 async-ready-null-adapter-v1 只管断言侧（站点 38:7／42:7），
// 本探针不简化也不改写这些站点的原 matcher。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_ASYNC_CRYPTO_BACKEND_TS_OBSERVATIONS
if (!output) throw new Error('缺少 AsyncCryptoBackend 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/primitives/AsyncCryptoBackend.ts')
// 与固定原测试的类型联合一致；用于把后端桩的 supportsCrypto 契约记成可比对的状态。
const OPERATIONS = ['signDigest', 'verifyDigest', 'verifyDigestBatch', 'publicKeyFromPrivate',
  'multiplyPublicKey', 'tweakPublicKeyAdd', 'tweakPrivateKeyAdd']
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/AsyncCryptoBackend\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('AsyncCryptoBackend 入口发生在固定测试之外')
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
    record(method, args, describe(result))
    return result
  } catch (error) {
    record(method, args, thrown(error))
    throw error
  } finally {
    depth--
  }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function bytesDescriptor (value) { return { kind: 'bytes', hex: hex(value) } }
function numberDescriptor (value) { return { kind: 'number', value: String(value) } }
function booleanDescriptor (value) { return { kind: 'boolean', value: Boolean(value) } }
function stringDescriptor (value) { return { kind: 'string', value: String(value) } }
function absentDescriptor () { return { kind: 'absent' } }
function numbersDescriptor (values) {
  return { kind: 'numbers', value: Array.from(values, value => numberDescriptor(value)) }
}
/** 后端桩的可观察状态：是否就绪、preload 次数、实际支持的操作集合。 */
function backendDescriptor (backend) {
  return { kind: 'backend', ready: Boolean(backend.isReady()), preloads: backend.preloads,
    supports: OPERATIONS.filter(operation => backend.supportsCrypto(operation)) }
}
/** 返回值：命中的后端实例仍是同一个桩后端，因此记录它的同一份可观察状态。 */
function backendResultDescriptor (value) {
  return value === undefined ? absentDescriptor() : backendDescriptor(value)
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function install (moduleObject) {
  const originals = {}
  for (const method of ['registerAsyncCryptoBackend', 'unregisterAsyncCryptoBackend',
    'readyAsyncCryptoBackend', 'isAsyncCryptoDigest', 'validateAsyncCryptoBytes']) {
    originals[method] = moduleObject[method]
  }
  moduleObject.registerAsyncCryptoBackend = function (...args) {
    return observe('registerAsyncCryptoBackend', [backendDescriptor(args[0])],
      () => Reflect.apply(originals.registerAsyncCryptoBackend, this, args), absentDescriptor)
  }
  moduleObject.unregisterAsyncCryptoBackend = function (...args) {
    return observe('unregisterAsyncCryptoBackend', [backendDescriptor(args[0])],
      () => Reflect.apply(originals.unregisterAsyncCryptoBackend, this, args), absentDescriptor)
  }
  moduleObject.readyAsyncCryptoBackend = function (...args) {
    return observe('readyAsyncCryptoBackend', [stringDescriptor(args[0])],
      () => Reflect.apply(originals.readyAsyncCryptoBackend, this, args), backendResultDescriptor)
  }
  moduleObject.isAsyncCryptoDigest = function (...args) {
    return observe('isAsyncCryptoDigest', [numbersDescriptor(args[0])],
      () => Reflect.apply(originals.isAsyncCryptoDigest, this, args), booleanDescriptor)
  }
  moduleObject.validateAsyncCryptoBytes = function (...args) {
    return observe('validateAsyncCryptoBytes',
      [stringDescriptor(args[0]), bytesDescriptor(args[1]),
        args.length > 2 && args[2] !== undefined ? numberDescriptor(args[2]) : absentDescriptor()],
      () => Reflect.apply(originals.validateAsyncCryptoBytes, this, args), bytesDescriptor)
  }
}

// 只包装一次并返回同一模块对象，避免 jest 工厂重入时拿到半包装的导出。
jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.readyAsyncCryptoBackend === undefined) return moduleObject
  installed = true
  install(moduleObject)
  return moduleObject
})
