// 固定 utils.test.ts：在公开函数入口记录真实实参，不修改原测试。
'use strict'
const fs = require('node:fs')
const path = require('node:path')
const { Buffer: NodeBuffer } = require('node:buffer')

const output = process.env.MIGRATION_UTILS_TS_OBSERVATIONS
if (!output) throw new Error('缺少 MIGRATION_UTILS_TS_OBSERVATIONS')
const testPath = expect.getState().testPath
if (!testPath.endsWith('/src/primitives/__tests/utils.test.ts')) throw new Error('固定 TS 文件不匹配')
const sdk = path.resolve(path.dirname(testPath), '../../..')
const modulePath = path.join(sdk, 'src/primitives/utils.ts')
const pointPath = path.join(sdk, 'src/primitives/Point.ts')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const methods = new Set([
  'toSafeString', 'toArray', 'hexToUint8Array', 'toUint8Array', 'zero2', 'toHex',
  'encode', 'fromBase58', 'toBase58', 'fromBase58Check', 'toBase58Check',
  'toUTF8', 'verifyNotNull', 'constantTimeEquals'
])
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let nextPointReceiverId = 0

beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  nextPointReceiverId = 0
})

function snapshot(value, seen = new Map()) {
  if (value === undefined) return { kind: 'Undefined' }
  if (value === null) return { kind: 'Null' }
  if (typeof value === 'string') return { kind: 'String', value }
  if (typeof value === 'number') return { kind: 'Number', value: Object.is(value, -0) ? '-0' : String(value) }
  if (typeof value === 'bigint') return { kind: 'BigInt', value: String(value) }
  if (typeof value === 'boolean') return { kind: 'Boolean', value }
  if (typeof value === 'symbol') return { kind: 'Symbol', description: value.description ?? null }
  if (typeof value === 'function') return { kind: 'Function', name: value.name }
  if (value instanceof Uint8Array) return { kind: 'Uint8Array', bytesHex: NodeBuffer.from(value).toString('hex') }
  if (value instanceof Error) return { kind: 'Error', name: value.name, message: value.message }
  if (seen.has(value)) return { kind: 'Ref', id: seen.get(value) }
  const id = seen.size + 1
  seen.set(value, id)
  if (Array.isArray(value)) return { kind: 'Array', id, value: Array.from(value, item => snapshot(item, seen)) }
  if (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null) {
    return { kind: 'Object', id, entries: Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, snapshot(item, seen)])) }
  }
  throw new Error(`utils 入口实参类型尚未表征：${value.constructor?.name || typeof value}`)
}

function sourceLine() {
  const match = new Error().stack.match(/\/utils\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('utils 入口调用缺少固定 TS 源码位置')
  return Number(match[1])
}

function observe(className, method, args, receiverId = 0, preState = { priorCalls: sequence }) {
  const test = expect.getState().currentTestName
  if (!test) return
  const row = { test, occurrence, sequence: ++sequence, receiverId,
    className, method, args: args.map(arg => snapshot(arg)), preState,
    source: { file: sourceFile, line: sourceLine() } }
  fs.appendFileSync(output, JSON.stringify(row) + '\n')
}

jest.doMock(modulePath, () => {
  const original = jest.requireActual(modulePath)
  const wrapped = { ...original }
  for (const method of methods) {
    // utils 与 Writer 存在循环导入；内层初始化可能只暴露部分 export。
    if (typeof original[method] !== 'function') continue
    wrapped[method] = function (...args) {
      observe('Utils', method, args)
      return Reflect.apply(original[method], this, args)
    }
  }
  return { ...wrapped, __esModule: true }
})

jest.doMock(pointPath, () => {
  const original = jest.requireActual(pointPath)
  if (typeof original.default !== 'function') return original
  const Point = new Proxy(original.default, {
    construct(target, args, newTarget) {
      const receiverId = ++nextPointReceiverId
      observe('Point', 'constructor', args, receiverId)
      const instance = Reflect.construct(target, args, newTarget)
      return new Proxy(instance, {
        get(object, property, receiver) {
          const value = Reflect.get(object, property, receiver)
          if (property !== 'encode') return value
          return function (...callArgs) {
            observe('Point', 'encode', callArgs, receiverId,
              { x: snapshot(object.x), y: snapshot(object.y), priorCalls: sequence })
            return Reflect.apply(value, object, callArgs)
          }
        }
      })
    }
  })
  return { ...original, default: Point, __esModule: true }
})
