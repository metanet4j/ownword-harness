// 固定 ProtoWallet.additional.test.ts：记录构造、公开方法实参与调用前 keyDeriver 状态。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_PROTOWALLET_ADDITIONAL_TS_INPUTS
if (!output) throw new Error('缺少 ProtoWallet.additional 原输入采集路径')
const sdk = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk')
const modulePath = path.join(sdk, 'src/wallet/ProtoWallet.ts')
const file = 'src/wallet/__tests/ProtoWallet.additional.test.ts'
const METHODS = ['getPublicKey', 'encrypt', 'decrypt', 'createHmac', 'verifyHmac', 'createSignature', 'verifySignature']
const occurrenceByTest = new Map()
const sequenceByTest = new Map()
let occurrence = 0
const originalCrypto = globalThis.crypto

/** 原测试用 PrivateKey.fromRandom() 建钱包；固定熵流让两端消费同一份密钥。 */
function installEntropy () {
  let state = 0x6d2b79f5
  const subtle = originalCrypto?.subtle
  // 保留 subtle 的原始接收者：派生对象上的 getter 会触发 Crypto 品牌检查。
  const seeded = { subtle, getRandomValues (array) {
    for (let index = 0; index < array.length; index++) {
      state ^= state << 13
      state ^= state >>> 17
      state ^= state << 5
      array[index] = state >>> 24
    }
    return array
  } }
  Object.defineProperty(globalThis, 'crypto', { configurable: true, value: seeded })
}

function current () { return expect.getState().currentTestName }
function lineOf () {
  const location = new Error().stack.match(/\/ProtoWallet\.additional\.test\.ts:(\d+):\d+/)
  if (!location) throw new Error('ProtoWallet.additional 入口缺少固定原测试调用站点')
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
  throw new Error('ProtoWallet.additional 原输入暂不支持：' + typeof value)
}
function deriverState (wallet) {
  return wallet?.keyDeriver === undefined || wallet?.keyDeriver === null ? 'undefined' : 'defined'
}
function record (method, args, state) {
  const test = current()
  if (!test) throw new Error('ProtoWallet.additional 入口发生在固定测试之外')
  const key = test + '\0' + occurrence
  const sequence = (sequenceByTest.get(key) || 0) + 1
  sequenceByTest.set(key, sequence)
  const row = { test, occurrence, sequence, source: { file, line: lineOf() }, className: 'ProtoWallet',
    method, args: args.map(arg => tag(arg)),
    preState: { priorEvents: sequence - 1, keyDeriver: state } }
  fs.appendFileSync(output, JSON.stringify(row) + '\n')
  return row
}

beforeEach(() => {
  installEntropy()
  const test = current()
  occurrence = (occurrenceByTest.get(test) || 0) + 1
  occurrenceByTest.set(test, occurrence)
})
afterEach(() => {
  Object.defineProperty(globalThis, 'crypto', { configurable: true, value: originalCrypto })
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  const Original = moduleObject.default
  const ProxyClass = new Proxy(Original, {
    construct (target, args, newTarget) {
      record('constructor', args, 'defined')
      const instance = Reflect.construct(target, args, newTarget)
      for (const name of METHODS) {
        const original = instance[name]
        if (typeof original !== 'function') throw new Error('ProtoWallet 缺少原方法：' + name)
        instance[name] = function (...methodArgs) {
          record(name, methodArgs, deriverState(this))
          return Reflect.apply(original, this, methodArgs)
        }
      }
      return instance
    }
  })
  return { ...moduleObject, __esModule: true, default: ProxyClass }
})
