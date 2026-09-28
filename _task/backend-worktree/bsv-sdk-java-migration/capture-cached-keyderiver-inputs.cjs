// 固定 CachedKeyDeriver.test.ts：记录构造与原测试直接发起的缓存方法调用。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_CACHED_KEYDERIVER_TS_INPUTS
if (!output) throw new Error('缺少 CachedKeyDeriver 原输入采集路径')
const sdk = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk')
const modulePath = path.join(sdk, 'src/wallet/CachedKeyDeriver.ts')
const file = 'src/wallet/__tests/CachedKeyDeriver.test.ts'
const METHODS = ['derivePublicKey', 'derivePrivateKey', 'derivePrivateKeys', 'deriveSymmetricKey',
  'revealCounterpartySecret', 'revealSpecificSecret']
const occurrenceByTest = new Map()
const sequenceByTest = new Map()
let occurrence = 0

function current () { return expect.getState().currentTestName }
function lineOf () {
  const location = new Error().stack.match(/\/CachedKeyDeriver\.test\.ts:(\d+):\d+/)
  if (!location) throw new Error('CachedKeyDeriver 入口缺少固定原测试调用站点')
  return Number(location[1])
}
function keyIdentity (value) {
  const name = value?.constructor?.name
  if (!['PublicKey', 'PrivateKey', 'SymmetricKey'].includes(name)) return null
  const hex = typeof value.toHex === 'function' ? value.toHex() : value.toString()
  return { kind: name, hex }
}
function derivation (value) {
  if (value === null || typeof value !== 'object') return null
  const names = Object.keys(value)
  if (!names.includes('protocolID') || !names.includes('keyID') || !names.includes('counterparty')) return null
  return { protocolID: value.protocolID, keyID: value.keyID, counterparty: value.counterparty }
}
function tag (value, seen = new Map()) {
  if (value === undefined) return { kind: 'Undefined' }
  if (value === null) return { kind: 'Null' }
  if (typeof value === 'string') return { kind: 'String', value }
  if (typeof value === 'boolean') return { kind: 'Boolean', value }
  if (typeof value === 'number') return { kind: 'Number', value: String(value) }
  const key = keyIdentity(value)
  if (key) return key
  const item = derivation(value)
  if (item) value = item
  if (Array.isArray(value)) {
    if (seen.has(value)) return { kind: 'Ref', id: seen.get(value) }
    const id = seen.size + 1; seen.set(value, id)
    return { kind: 'Array', id, value: value.map(entry => tag(entry, seen)) }
  }
  if (typeof value === 'object') {
    if (seen.has(value)) return { kind: 'Ref', id: seen.get(value) }
    const id = seen.size + 1; seen.set(value, id)
    const entries = {}
    for (const name of Object.keys(value).sort()) entries[name] = tag(value[name], seen)
    return { kind: 'Object', id, entries }
  }
  throw new Error('CachedKeyDeriver 原输入暂不支持：' + typeof value)
}
function record (method, args) {
  const test = current()
  if (!test) throw new Error('CachedKeyDeriver 入口发生在固定测试之外')
  const key = test + '\0' + occurrence
  const sequence = (sequenceByTest.get(key) || 0) + 1
  sequenceByTest.set(key, sequence)
  const row = { test, occurrence, sequence, source: { file, line: lineOf() }, className: 'CachedKeyDeriver',
    method, args: args.map(arg => tag(arg)), preState: { priorEvents: sequence - 1 } }
  fs.appendFileSync(output, JSON.stringify(row) + '\n')
  return row
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrenceByTest.get(test) || 0) + 1
  occurrenceByTest.set(test, occurrence)
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  const Original = moduleObject.default
  const ProxyClass = new Proxy(Original, {
    construct (target, args, newTarget) {
      record('constructor', args)
      const instance = Reflect.construct(target, args, newTarget)
      for (const name of METHODS) {
        const original = instance[name]
        if (typeof original !== 'function') throw new Error('CachedKeyDeriver 缺少原方法：' + name)
        instance[name] = function (...methodArgs) {
          record(name, methodArgs)
          return Reflect.apply(original, this, methodArgs)
        }
      }
      return instance
    }
  })
  return { ...moduleObject, __esModule: true, default: ProxyClass }
})
