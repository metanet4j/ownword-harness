// 固定 HMAC 原测试：记录 SHA256HMAC 构造和公开方法的真实入参及此前实际调用。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_HMAC_TS_OBSERVATIONS
if (!output) throw new Error('缺少 MIGRATION_HMAC_TS_OBSERVATIONS')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const modulePath = path.join(sdk, 'src/primitives/Hash.ts')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let receiverIndex = 0

beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  receiverIndex = 0
})

function snapshot (value) {
  if (value === undefined) return { kind: 'Undefined' }
  if (value === null) return { kind: 'Null' }
  if (typeof value === 'string') return { kind: 'String', value }
  if (typeof value === 'number') return { kind: 'Number', value: String(value) }
  if (Array.isArray(value)) return { kind: 'ByteArray', bytesHex: Buffer.from(value).toString('hex') }
  if (value instanceof Uint8Array) return { kind: 'Uint8Array', bytesHex: Buffer.from(value).toString('hex') }
  throw new Error(`HMAC 实参类型尚未表征：${value?.constructor?.name || typeof value}`)
}

function location () {
  const escaped = path.basename(testPath).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const match = new Error().stack.match(new RegExp(`${escaped}:(\\d+):\\d+`))
  return match ? Number(match[1]) : null
}

function observe (receiverId, method, args, before) {
  const test = expect.getState().currentTestName
  if (!test) return
  const line = location()
  if (line === null) throw new Error('HMAC 原测试调用缺少源码位置')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    receiverId, className: 'SHA256HMAC', method, args: args.map(snapshot), preState: before,
    source: { file: sourceFile, line } }) + '\n')
}

function wrap (target, receiverId) {
  const updates = []
  let proxy
  proxy = new Proxy(target, {
    get (object, property) {
      const value = Reflect.get(object, property, object)
      if (property !== 'update' && property !== 'digestHex') return value
      return function (...args) {
        const before = { blockSize: object.blockSize, outSize: object.outSize,
          priorCalls: updates.map(call => call.map(snapshot)) }
        observe(receiverId, property, args, before)
        const result = Reflect.apply(value, object, args)
        if (property === 'update') updates.push(args)
        return result === object ? proxy : result
      }
    }
  })
  return proxy
}

jest.doMock(modulePath, () => {
  const original = jest.requireActual(modulePath)
  const SHA256HMAC = new Proxy(original.SHA256HMAC, {
    construct (target, args, newTarget) {
      const receiverId = ++receiverIndex
      observe(receiverId, 'constructor', args, null)
      return wrap(Reflect.construct(target, args, newTarget), receiverId)
    }
  })
  return { ...original, SHA256HMAC, __esModule: true }
})
