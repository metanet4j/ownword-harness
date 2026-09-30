// 固定 AESGCM.man.test.ts 原输入与原断言轨迹。
//
// 原用例分配 2^29+16 字节明文并把解密结果逐字节与明文比较；AESGCM／AESGCMDecrypt 的实参与
// 返回值因此都是 512 MiB 级字节数组。沿用既有 symmetric-manual／wallet-wire 的口径：
// 超过 65536 字节的数组记成「长度 + SHA-256」摘要（Java 侧 ParityRecorder.digestSummary 同形），
// 内存中的逐字节比较仍由原测试自己执行，摘要只用于跨语言比对。
//
// 断言轨迹仍由 capture-parity.cjs 采集；只有 `expect(<大数组>).not.toBeNull()`（站点 25:5）
// 必须在本探针内拦截：通用采集器会把 512 MiB 实际值展开成 JSON，既不可行也超出既有口径。
// 拦截行按通用采集器的行格式写出（matcher／negated／index／expected／pass 语义相同），
// 其它 matcher 一律原样委托给当前断言采集器。
'use strict'
const crypto = require('node:crypto')
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_AESGCM_MAN_TS_OBSERVATIONS
if (!output) throw new Error('缺少 AESGCM.man 原输入采集路径')
const assertions = process.env.MIGRATION_PARITY_TS_OBSERVATIONS
const LARGE_THRESHOLD = 65536
// 探针先于断言采集器加载（--setupFilesAfterEnv 顺序／分派表 require），这里拿到原生 Jest expect。
const nativeExpect = global.expect
const testPath = nativeExpect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/primitives/AESGCM.ts')
const occurrences = new Map()
const assertionCounters = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false
let wrapperInstalled = false

function current () { return nativeExpect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/AESGCM\.man\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
// update 直接接收 Uint8Array，避免 512 MiB 数组再复制一份。
function sha256 (bytes) { return crypto.createHash('sha256').update(bytes).digest('hex') }
/** 与 Java ParityRecorder.digestSummary 完全同形的摘要描述。 */
function digest (bytes) {
  return { type: 'map', value: {
    length: { type: 'number', value: String(bytes.length) },
    sha256: { type: 'string', value: sha256(bytes) }
  } }
}
function bytesDescriptor (value) {
  const bytes = value instanceof Uint8Array ? value : Uint8Array.from(value)
  if (bytes.length > LARGE_THRESHOLD) return digest(bytes)
  return { kind: 'bytes', hex: Buffer.from(bytes).toString('hex') }
}
function resultDescriptor (value) {
  return { kind: 'result', result: bytesDescriptor(value.result), authenticationTag: bytesDescriptor(value.authenticationTag) }
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('AESGCM.man 入口发生在固定测试之外')
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

function isLargeBytes (value) {
  return (value instanceof Uint8Array || Buffer.isBuffer(value)) && value.length > LARGE_THRESHOLD
}
/** 站点 25:5 的 `expect(decrypted).not.toBeNull()`：记录摘要形状，真值仍由原生 Jest 断言判定。 */
function assertNull (received, negated, args) {
  const receiver = nativeExpect(received)
  const target = negated ? receiver.not : receiver
  let failure = null
  try {
    return Reflect.apply(target.toBeNull, target, args)
  } catch (error) {
    failure = error
    throw error
  } finally {
    if (!assertions) throw new Error('缺少 MIGRATION_PARITY_TS_OBSERVATIONS')
    const test = current()
    const matcher = (negated ? 'not.' : '') + 'toBeNull'
    const key = test + ':' + matcher
    const index = (assertionCounters.get(key) || 0) + 1
    assertionCounters.set(key, index)
    fs.appendFileSync(assertions, JSON.stringify({ test, file: path.normalize(nativeExpect.getState().testPath || ''),
      occurrence, index, matcher, negated, actual: digest(received), expected: [], pass: failure === null }) + '\n')
  }
}
function intercept (delegate, received) {
  const negatedProxy = new Proxy(delegate.not, {
    get (target, property) {
      if (property === 'toBeNull') return (...args) => assertNull(received, true, args)
      const value = target[property]
      return typeof value === 'function' ? value.bind(target) : value
    }
  })
  return new Proxy(delegate, {
    get (target, property) {
      if (property === 'not') return negatedProxy
      if (property === 'toBeNull') return (...args) => assertNull(received, false, args)
      const value = target[property]
      return typeof value === 'function' ? value.bind(target) : value
    }
  })
}
function installExpectWrapper () {
  if (wrapperInstalled) return
  wrapperInstalled = true
  const delegate = global.expect
  function wrapped (received) {
    const assertion = delegate(received)
    return isLargeBytes(received) ? intercept(assertion, received) : assertion
  }
  Object.assign(wrapped, delegate)
  global.expect = wrapped
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  installExpectWrapper()
})

function install (moduleObject) {
  const originals = { AESGCM: moduleObject.AESGCM, AESGCMDecrypt: moduleObject.AESGCMDecrypt }
  moduleObject.AESGCM = function (...args) {
    return observe('AESGCM', args.map(bytesDescriptor),
      () => Reflect.apply(originals.AESGCM, this, args), resultDescriptor)
  }
  moduleObject.AESGCMDecrypt = function (...args) {
    return observe('AESGCMDecrypt', args.map(bytesDescriptor),
      () => Reflect.apply(originals.AESGCMDecrypt, this, args), bytesDescriptor)
  }
}

// 只包装一次并返回同一模块对象，避免 jest 工厂重入时拿到半包装的导出。
jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.AESGCM === undefined) return moduleObject
  installed = true
  install(moduleObject)
  return moduleObject
})
