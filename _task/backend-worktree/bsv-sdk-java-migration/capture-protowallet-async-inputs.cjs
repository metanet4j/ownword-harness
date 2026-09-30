// 固定 ProtoWallet.async-backend.test.ts：从桶文件出口替换 ProtoWallet/KeyDeriver，并记录异步后端注册。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_PROTOWALLET_ASYNC_TS_INPUTS
if (!output) throw new Error('缺少 ProtoWallet.async-backend 原输入采集路径')
const sdk = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk')
const modulePath = path.join(sdk, 'src/wallet/ProtoWallet.ts')
const file = 'src/wallet/__tests/ProtoWallet.async-backend.test.ts'
const METHODS = ['getPublicKey', 'encrypt', 'decrypt', 'createHmac', 'verifyHmac', 'createSignature',
  'verifySignature', 'revealCounterpartyKeyLinkage', 'revealSpecificKeyLinkage']
const occurrenceByTest = new Map()
const sequenceByTest = new Map()
let occurrence = 0
const originalCrypto = globalThis.crypto
const originalDate = globalThis.Date
function current () { return expect.getState().currentTestName }
/** 立即调用者不是原测试时属于实现内部自调用，不进入边界账本。 */
function fromTest () {
  const frames = new Error().stack.split('\n').slice(1)
  const caller = frames.find(frame => /ProtoWallet\.(async-backend\.test\.ts|ts)/.test(frame))
  return Boolean(caller && /ProtoWallet\.async-backend\.test\.ts/.test(caller))
}
function lineOf () {
  const location = new Error().stack.match(/\/ProtoWallet\.async-backend\.test\.ts:(\d+):\d+/)
  if (!location) throw new Error('ProtoWallet.async-backend 入口缺少固定原测试调用站点')
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
  throw new Error('ProtoWallet.async-backend 原输入暂不支持：' + typeof value)
}
function record (method, args, className = 'ProtoWallet') {
  const test = current()
  if (!test) throw new Error('ProtoWallet.async-backend 入口发生在固定测试之外')
  const key = test + '\0' + occurrence
  const sequence = (sequenceByTest.get(key) || 0) + 1
  sequenceByTest.set(key, sequence)
  const row = { test, occurrence, sequence, source: { file, line: lineOf() }, className,
    method, args: args.map(arg => tag(arg)), preState: { priorEvents: sequence - 1 } }
  fs.appendFileSync(output, JSON.stringify(row) + '\n')
  return row
}

function installFixedTime () {
  class FixedDate extends originalDate {
    constructor (...args) { super(...(args.length === 0 ? [FIXED_TIME] : args)) }
    static now () { return FIXED_TIME }
  }
  Object.defineProperty(globalThis, 'Date', { configurable: true, value: FixedDate })
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrenceByTest.get(test) || 0) + 1
  occurrenceByTest.set(test, occurrence)
})
const barrelPath = path.join(sdk, 'mod.ts')
const deriverPath = path.join(sdk, 'src/wallet/KeyDeriver.ts')
const OPERATIONS = ['signDigest', 'verifyDigest', 'verifyDigestBatch', 'publicKeyFromPrivate',
  'multiplyPublicKey', 'tweakPublicKeyAdd', 'tweakPrivateKeyAdd']

function backendShape (backend) {
  return { supported: OPERATIONS.filter(operation => backend.supportsCrypto(operation)) }
}
function wrapWallet (Original) {
  return new Proxy(Original, {
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
}
function wrapDeriver (Original) {
  return new Proxy(Original, {
    construct (target, args, newTarget) {
      record('constructor', args, 'KeyDeriver')
      const instance = Reflect.construct(target, args, newTarget)
      const original = instance.deriveSymmetricKeyAsync
      if (typeof original !== 'function') throw new Error('KeyDeriver 缺少 deriveSymmetricKeyAsync')
      instance.deriveSymmetricKeyAsync = function (...methodArgs) {
        if (fromTest()) record('deriveSymmetricKeyAsync', methodArgs, 'KeyDeriver')
        return Reflect.apply(original, this, methodArgs)
      }
      return instance
    }
  })
}

jest.doMock(barrelPath, () => {
  const moduleObject = jest.requireActual(barrelPath)
  return {
    ...moduleObject,
    ProtoWallet: wrapWallet(moduleObject.ProtoWallet),
    KeyDeriver: wrapDeriver(moduleObject.KeyDeriver),
    registerAsyncCryptoBackend: backend => {
      record('registerAsyncCryptoBackend', [backendShape(backend)], 'AsyncCryptoBackend')
      return moduleObject.registerAsyncCryptoBackend(backend)
    },
    unregisterAsyncCryptoBackend: backend => {
      record('unregisterAsyncCryptoBackend', [backendShape(backend)], 'AsyncCryptoBackend')
      return moduleObject.unregisterAsyncCryptoBackend(backend)
    }
  }
})
