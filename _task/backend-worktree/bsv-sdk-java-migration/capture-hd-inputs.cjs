// 固定 HD.test.ts 的 49 个原用例输入：fromRandom／fromString／fromSeed／fromBinary 四个入口与
// toString／toPublic／toBinary／derive／isPrivate。HD 与自身静态方法互相调用，因此用真实模块
// 只包装原型与静态方法；随机来源（fromRandom）只登记可比观察（前缀／字节长度），确定性向量
// （seed、派生路径、二进制往返）逐值比较。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_HD_TS_OBSERVATIONS
if (!output) throw new Error('缺少 HD 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/compat/HD.ts')
// 原测试的随机来源必须与 Java 侧 CompatRandom 完全一致：否则 fromRandom 生成的实例
// 在断言（not.toEqual 两个随机 xprv）上永远无法逐值对齐。这里按 HDTest.randomBytes
// 的同一 xorshift 流播种 getRandomValues，消费顺序与 Java 的 @BeforeAll + 49 个用例一致。
const ENTROPY_STATE = { value: 0x243f6a88 }
const originalCrypto = globalThis.crypto
function seededRandomBytes (length) {
  const out = new Uint8Array(length)
  for (let index = 0; index < length; index++) {
    ENTROPY_STATE.value = (ENTROPY_STATE.value ^ (ENTROPY_STATE.value << 13)) >>> 0
    ENTROPY_STATE.value = (ENTROPY_STATE.value ^ (ENTROPY_STATE.value >>> 17)) >>> 0
    ENTROPY_STATE.value = (ENTROPY_STATE.value ^ (ENTROPY_STATE.value << 5)) >>> 0
    out[index] = ENTROPY_STATE.value & 0xff
  }
  return out
}
Object.defineProperty(globalThis, 'crypto', {
  configurable: true,
  value: { subtle: originalCrypto?.subtle, getRandomValues (array) {
    const bytes = seededRandomBytes(array.length)
    for (let index = 0; index < array.length; index++) array[index] = bytes[index]
    return array
  } }
})
const occurrences = new Map()
const entryCounts = new Map()
// 随机生成的 HD：结果不可逐值比较，只登记 xprv／xpub 前缀与字节长度。
const randomInstances = new WeakSet()
let activeTest = null
let activeOccurrence = 0
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/HD\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, test = activeTest, at = activeOccurrence, line = callLine()) {
  if (!test) return
  const key = `${test}\0${at}`
  entryCounts.set(key, (entryCounts.get(key) || 0) + 1)
  fs.appendFileSync(output, JSON.stringify({ test, occurrence: at, sequence: ++sequence,
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
function describeNumberArray (values) {
  return { kind: 'numberArray', hex: hex(Uint8Array.from(values)), length: values.length }
}
function describeText (value) { return { kind: 'string', value } }
function describeBoolean (value) { return { kind: 'boolean', value } }
function describeHd (hd) {
  if (hd === null || hd === undefined) return null
  const text = hd.toString()
  return randomInstances.has(hd) ? { kind: 'hd', prefix: text.slice(0, 4) } : { kind: 'hd', value: text }
}

beforeEach(() => {
  activeTest = current()
  occurrence = (occurrences.get(activeTest) || 0) + 1
  occurrences.set(activeTest, occurrence)
  activeOccurrence = occurrence
  sequence = 0
})

afterEach(() => {
  // 原文件的 #toString 用例在 describe 体内创建随机 HD，这里只登记测试内的入口；
  // 若某个用例完全没有可观测入口则发出固定标记，Java 侧在对应位置发出同一条目。
  if (activeTest && !entryCounts.has(`${activeTest}\0${activeOccurrence}`)) {
    record('noEntryPoint', [], null, activeTest, activeOccurrence, null)
  }
  activeTest = null
  activeOccurrence = 0
})

function install (Original) {
  const statics = {}
  for (const method of ['fromRandom', 'fromString', 'fromSeed', 'fromBinary']) statics[method] = Original[method]
  const methods = {}
  for (const method of ['fromRandom', 'fromString', 'fromSeed', 'fromBinary', 'toString', 'toPublic',
    'toBinary', 'derive', 'isPrivate']) methods[method] = Original.prototype[method]

  const loadRandom = (target, args, action) => observe('fromRandom', [], () => {
    const hd = action()
    randomInstances.add(hd)
    return hd
  }, describeHd)
  Original.fromRandom = function (...args) {
    return loadRandom(this, args, () => Reflect.apply(statics.fromRandom, this, args))
  }
  Original.prototype.fromRandom = function (...args) {
    return loadRandom(this, args, () => Reflect.apply(methods.fromRandom, this, args))
  }
  Original.fromString = function (...args) {
    return observe('fromString', [describeText(args[0])],
      () => Reflect.apply(statics.fromString, this, args), describeHd)
  }
  Original.fromSeed = function (...args) {
    return observe('fromSeed', [describeNumberArray(args[0])],
      () => Reflect.apply(statics.fromSeed, this, args), describeHd)
  }
  Original.fromBinary = function (...args) {
    return observe('fromBinary', [describeNumberArray(args[0])],
      () => Reflect.apply(statics.fromBinary, this, args), describeHd)
  }
  Original.prototype.toString = function (...args) {
    return observe('toString', [], () => {
      try {
        return Reflect.apply(methods.toString, this, args)
      } catch (error) {
        // 空 HD（没有版本字节）无法序列化；采集器的对象观察会对实例调用 String()，
        // 这里回退为 JS 普通对象的显示形式，与 Java 侧同一退化的观察一致。
        return '[object Object]'
      }
    }, value => randomInstances.has(this) ? { kind: 'string', prefix: value.slice(0, 4) } : { kind: 'string', value })
  }
  Original.prototype.toPublic = function (...args) {
    return observe('toPublic', [], () => {
      const hd = Reflect.apply(methods.toPublic, this, args)
      if (randomInstances.has(this)) randomInstances.add(hd)
      return hd
    }, describeHd)
  }
  Original.prototype.toBinary = function (...args) {
    return observe('toBinary', [], () => Reflect.apply(methods.toBinary, this, args),
      value => randomInstances.has(this) ? { kind: 'numberArray', length: value.length } : describeNumberArray(value))
  }
  Original.prototype.derive = function (...args) {
    return observe('derive', [describeText(args[0])], () => {
      const hd = Reflect.apply(methods.derive, this, args)
      if (randomInstances.has(this)) randomInstances.add(hd)
      return hd
    }, describeHd)
  }
  Original.prototype.isPrivate = function (...args) {
    return observe('isPrivate', [], () => Reflect.apply(methods.isPrivate, this, args), describeBoolean)
  }
}

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  install(moduleObject.default)
  return moduleObject
})
