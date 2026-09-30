// 固定 Hash.additional.test.ts 的原输入：只登记原测试真实发起的 Hash 公开入口调用。
// 结果按原语言实际观察形状记录：字节数组、十六进制字符串或异常；
// 链式返回 this 的 update 不跨语言可比，按 void 记录（消息本身已随实参登记）。
//
// 这里原地包装已加载模块的导出，不用 jest.doMock：纯 TS 回退用例
// （matches native digests when node:crypto is unavailable）用 jest.isolateModules 重新加载
// Hash.ts，必须让那次求值真的在 getBuiltinModule 被屏蔽后发生；doMock 工厂里的
// jest.requireActual 会拿到外层已求值的实例，使回退分支退化为 node:crypto 路径。
// 该用例没有可包装的 SDK 入口，改为登记测试自己的十六进制转换（toHex 辅助）。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_HASH_ADDITIONAL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Hash.additional 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/primitives/Hash.ts')
const FALLBACK_TEST = 'Hash – additional coverage pure-TS fallback parity matches native digests when node:crypto is unavailable'
const FALLBACK_RANGE = [100, 130]

const nativeBufferFrom = Buffer.from
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let recording = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/Hash\.additional\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('Hash.additional 入口缺少固定原测试调用位置')
  return Number(match[1])
}
/** 纯 TS 回退用例的 toHex 辅助调用位置；其余调用（框架与探针内部）不进入账本。 */
function fallbackLine () {
  if (current() !== FALLBACK_TEST) return null
  // toHex 辅助自身的帧在前，用例调用点在后：取本文件里落在该用例范围内的帧。
  const lines = []
  for (const match of new Error().stack.matchAll(/Hash\.additional\.test\.ts:(\d+):\d+/g)) {
    lines.push(Number(match[1]))
  }
  const hit = lines.find(line => line >= FALLBACK_RANGE[0] && line <= FALLBACK_RANGE[1])
  return hit === undefined ? null : hit
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('Hash.additional 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function observe (method, args, action, describe) {
  if (depth !== 0) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? outcome(result) : describe(result))
    return result
  } catch (error) {
    record(method, args, thrown(error))
    throw error
  } finally {
    depth--
  }
}
function hex (bytes) { return nativeBufferFrom(bytes).toString('hex') }
function string (value) { return { kind: 'string', value: String(value) } }
function number (value) { return { kind: 'number', value: String(value) } }
function undefinedValue () { return { kind: 'undefined' } }
function encoding (value) { return value === undefined || value === null ? undefinedValue() : string(value) }
function numberArray (value) {
  const list = Uint8Array.from(value)
  return { kind: 'numberArray', length: list.length, hex: hex(list) }
}
function argument (value) {
  if (value === undefined || value === null) return undefinedValue()
  if (typeof value === 'string') return string(value)
  if (typeof value === 'number') return number(value)
  return numberArray(value)
}
function outcome (value) {
  if (typeof value === 'string') return string(value)
  if (value === undefined || value === null) return undefinedValue()
  if (typeof value === 'object' && typeof value.length === 'number') return numberArray(value)
  // update 返回 this：实例状态不可跨语言比较，按 void 记录。
  return { kind: 'void' }
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw',
    name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function install () {
  const moduleObject = require(modulePath)
  for (const name of ['sha256', 'sha512', 'ripemd160', 'hash256', 'hash160']) {
    const original = moduleObject[name]
    if (typeof original !== 'function') continue
    moduleObject[name] = function (...args) {
      return observe(name, [argument(args[0]), encoding(args[1])],
        () => Reflect.apply(original, this, args))
    }
  }
  for (const name of ['sha256hmac', 'sha512hmac']) {
    const original = moduleObject[name]
    if (typeof original !== 'function') continue
    moduleObject[name] = function (...args) {
      return observe(name, [argument(args[0]), argument(args[1]), encoding(args[2])],
        () => Reflect.apply(original, this, args))
    }
  }
  const toArrayOriginal = moduleObject.toArray
  moduleObject.toArray = function (...args) {
    return observe('toArray', [argument(args[0]), encoding(args[1])],
      () => Reflect.apply(toArrayOriginal, this, args))
  }
  const pbkdf2Original = moduleObject.pbkdf2
  moduleObject.pbkdf2 = function (...args) {
    return observe('pbkdf2', args.map(argument),
      () => Reflect.apply(pbkdf2Original, this, args))
  }
  for (const name of ['SHA1HMAC', 'SHA512HMAC']) {
    const Original = moduleObject[name]
    if (typeof Original !== 'function') continue
    const originals = { update: Original.prototype.update, digest: Original.prototype.digest,
      digestHex: Original.prototype.digestHex }
    Original.prototype.update = function (...args) {
      return observe('update', [argument(args[0]), encoding(args[1])],
        () => Reflect.apply(originals.update, this, args))
    }
    Original.prototype.digest = function (...args) {
      return observe('digest', [], () => Reflect.apply(originals.digest, this, args))
    }
    Original.prototype.digestHex = function (...args) {
      return observe('digestHex', [], () => Reflect.apply(originals.digestHex, this, args))
    }
  }
}

install()

// 纯 TS 回退用例里没有可登记的 SDK 入口：登记测试自己的字节→十六进制转换结果。
Buffer.from = function (...args) {
  const result = Reflect.apply(nativeBufferFrom, this, args)
  const line = recording ? null : fallbackLine()
  if (line !== null) {
    recording = true
    try {
      record('toHex', [argument(args[0])], string(result.toString('hex')), line)
    } finally {
      recording = false
    }
  }
  return result
}
