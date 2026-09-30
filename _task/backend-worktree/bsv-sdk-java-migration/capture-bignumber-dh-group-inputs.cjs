// 固定 BigNumber.dhGroup.test.ts 的原输入：只登记原测试真实发起的 BigNumber 构造与归约结果。
// toRed 与 redPow 的中间红数不可跨语言比较，登记的是同一调用链上可比的部分：
// 三个构造实参、fromRed 的实际值与最终 toArray 的字节。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_BIGNUMBER_DH_GROUP_TS_OBSERVATIONS
if (!output) throw new Error('缺少 BigNumber.dhGroup 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/primitives/BigNumber.ts')

const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

function current () { return expect.getState().currentTestName }
/**
 * 只有直接由本原测试文件发起、或经由 Red 运算链发起的调用才登记。
 * 沿栈向上取“第一个提到原测试文件或 BigNumber.ts 的帧”：先撞到 BigNumber.ts 说明是模块
 * 内部构造（例如 redPow 内部的 new BigNumber(1)），不入账。
 */
function callLine () {
  for (const frame of new Error().stack.split('\n')) {
    const test = frame.match(/BigNumber\.dhGroup\.test\.ts:(\d+):\d+/)
    if (test) return Number(test[1])
    if (/src\/primitives\/BigNumber\.ts:/.test(frame)) return null
  }
  return null
}
function record (method, args, result, line = callLine()) {
  if (line === null) return false
  const test = current()
  if (!test) return false
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
  return true
}
function observe (method, args, action, describe) {
  if (depth !== 0) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? bigNumber(result) : describe(result))
    return result
  } catch (error) {
    record(method, args, thrown(error))
    throw error
  } finally {
    depth--
  }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function string (value) { return { kind: 'string', value: String(value) } }
function number (value) { return { kind: 'number', value: String(value) } }
function bigNumber (value) { return { kind: 'bigNumber', value: String(value) } }
function numberArray (value) {
  const list = Uint8Array.from(value)
  return { kind: 'numberArray', length: list.length, hex: hex(list) }
}
function argument (value) { return typeof value === 'string' ? string(value) : number(value) }
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

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  const Original = moduleObject.default
  const originals = { fromRed: Original.prototype.fromRed, toArray: Original.prototype.toArray }
  Original.prototype.fromRed = function (...args) {
    return observe('fromRed', [], () => Reflect.apply(originals.fromRed, this, args), bigNumber)
  }
  Original.prototype.toArray = function (...args) {
    return observe('toArray', [], () => Reflect.apply(originals.toArray, this, args), numberArray)
  }
  const ProxyClass = new Proxy(Original, {
    construct (target, args, newTarget) {
      return observe('constructor', [argument(args[0])].concat(args.length > 1 ? [number(args[1])] : []),
        () => Reflect.construct(target, args, newTarget), value => bigNumber(value))
    }
  })
  return { ...moduleObject, __esModule: true, default: ProxyClass }
})
