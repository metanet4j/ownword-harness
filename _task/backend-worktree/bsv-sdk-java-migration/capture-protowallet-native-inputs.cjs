// 固定 ProtoWallet.native-hash.test.ts：记录签名/验签入口；钱包在 describe 体内构造，
// 归到该 describe 首个执行用例之前。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_PROTOWALLET_NATIVE_TS_INPUTS
if (!output) throw new Error('缺少 ProtoWallet.native-hash 原输入采集路径')
const sdk = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk')
const modulePath = path.join(sdk, 'src/wallet/ProtoWallet.ts')
const file = 'src/wallet/__tests/ProtoWallet.native-hash.test.ts'
const METHODS = ['createSignature', 'verifySignature']
const occurrenceByTest = new Map()
const sequenceByTest = new Map()
let occurrence = 0
const originalCrypto = globalThis.crypto
const originalDate = globalThis.Date
function current () { return expect.getState().currentTestName }
/** 立即调用者不是原测试时属于实现内部自调用，不进入边界账本。 */
function fromTest () {
  const frames = new Error().stack.split('\n').slice(1)
  const caller = frames.find(frame => /ProtoWallet\.(native-hash\.test\.ts|ts)/.test(frame))
  return Boolean(caller && /ProtoWallet\.native-hash\.test\.ts/.test(caller))
}
function lineOf () {
  const location = new Error().stack.match(/\/ProtoWallet\.native-hash\.test\.ts:(\d+):\d+/)
  if (!location) throw new Error('ProtoWallet.native-hash 入口缺少固定原测试调用站点')
  return Number(location[1])
}
function keyIdentity (value) {
  if (value?.constructor?.name !== 'PrivateKey') return null
  return { kind: 'PrivateKey', hex: typeof value.toHex === 'function' ? value.toHex() : value.toString() }
}
function tag (value, seen = new Map()) {
  if (value === undefined) return { kind: 'Undefined' }
  if (value === null) return { kind: 'Null' }
  if (typeof value === 'string') return { kind: 'String', value }
  if (typeof value === 'boolean') return { kind: 'Boolean', value }
  if (typeof value === 'number') return { kind: 'Number', value: String(value) }
  const key = keyIdentity(value)
  if (key) return key
  if (Array.isArray(value)) {
    if (seen.has(value)) return { kind: 'Ref', id: seen.get(value) }
    const id = seen.size + 1; seen.set(value, id)
    return { kind: 'Array', id, value: value.map(item => tag(item, seen)) }
  }
  if (typeof value === 'object') {
    if (seen.has(value)) return { kind: 'Ref', id: seen.get(value) }
    const id = seen.size + 1; seen.set(value, id)
    const entries = {}
    for (const name of Object.keys(value).sort()) entries[name] = tag(value[name], seen)
    return { kind: 'Object', id, entries }
  }
  throw new Error('ProtoWallet.native-hash 原输入暂不支持：' + typeof value)
}
const pendingConstructors = []
/** describe 体内构造的钱包在任何用例之前，缓冲后作为该用例的首个入口记录。 */
function flush (entries) {
  const test = current()
  const key = test + '\0' + occurrence
  for (const entry of entries) {
    const sequence = (sequenceByTest.get(key) || 0) + 1
    sequenceByTest.set(key, sequence)
    const row = { test, occurrence, sequence, source: { file, line: entry.line }, className: 'ProtoWallet',
      method: entry.method, args: entry.args.map(arg => tag(arg)), preState: { priorEvents: sequence - 1 } }
    fs.appendFileSync(output, JSON.stringify(row) + '\n')
  }
}
function record (method, args) {
  const test = current()
  if (!test) {
    if (method !== 'constructor') throw new Error('ProtoWallet.native-hash 入口发生在固定测试之外')
    pendingConstructors.push({ method, args, line: 0 })
    return null
  }
  const entries = pendingConstructors.splice(0)
  entries.push({ method, args, line: lineOf() })
  flush(entries)
  return entries[entries.length - 1]
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
        if (typeof original !== 'function') throw new Error('ProtoWallet 缺少原方法：' + name)
        instance[name] = function (...methodArgs) {
          if (fromTest()) record(name, methodArgs)
          return Reflect.apply(original, this, methodArgs)
        }
      }
      return instance
    }
  })
  return { ...moduleObject, __esModule: true, default: ProxyClass }
})
