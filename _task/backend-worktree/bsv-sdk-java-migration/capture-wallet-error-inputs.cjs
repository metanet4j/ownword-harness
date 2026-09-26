// 固定 WalletError.test.ts 的公开构造器、序列化入口和枚举读取实参。
'use strict'
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.MIGRATION_WALLET_ERROR_TS_INPUTS
if (!output) throw new Error('缺少 WalletError 输入采集路径')
const sdk = path.resolve(path.dirname(expect.getState().testPath), '../../..')
const modulePath = path.join(sdk, 'src/wallet/WalletError.ts')

function tagged(value, seen = new WeakSet()) {
  if (value === undefined) return { type: 'undefined' }
  if (value === null) return { type: 'null' }
  if (typeof value === 'boolean' || typeof value === 'string') return { type: typeof value, value }
  if (typeof value === 'number') {
    const bits = Buffer.alloc(8)
    bits.writeDoubleBE(value)
    return { type: 'number', bits: bits.toString('hex') }
  }
  if (typeof value !== 'object') throw new Error('未支持的 WalletError 入参类型：' + typeof value)
  if (seen.has(value)) return { type: 'cycle' }
  seen.add(value)
  try {
    if (value instanceof Uint8Array) return { type: 'Uint8Array', bytes: Array.from(value) }
    if (Array.isArray(value)) return { type: 'array', value: value.map(item => tagged(item, seen)) }
    const entries = Object.entries(value).map(([key, item]) => ({ key, value: tagged(item, seen) }))
    if (value instanceof Error) return {
      type: 'error', constructor: value.constructor.name, message: value.message, entries
    }
    return { type: 'object', entries }
  } finally {
    seen.delete(value)
  }
}

function record(method, args) {
  const test = expect.getState().currentTestName
  const location = new Error().stack.match(/\/WalletError\.test\.ts:(\d+):\d+/)
  if (!test || !location) return
  fs.appendFileSync(output, JSON.stringify({ test, line: Number(location[1]), method,
    args: args.map(item => tagged(item)) }) + '\n')
}

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  const Original = moduleObject.WalletError
  let Wrapped
  Wrapped = new Proxy(Original, {
    construct(target, args, newTarget) {
      if (newTarget === Wrapped) record('WalletError', args)
      return Reflect.construct(target, args, newTarget)
    },
    get(target, property, receiver) {
      if (property !== 'unknownToJson') return Reflect.get(target, property, receiver)
      return function (...args) {
        record('unknownToJson', args)
        return Reflect.apply(target.unknownToJson, this, args)
      }
    }
  })
  // 原测试校验 captureStackTrace 的第二个实参；代理仍代表同一个构造器身份。
  Original.prototype.constructor = Wrapped
  const enumView = new Proxy(moduleObject.walletErrors, {
    get(target, property, receiver) {
      if (typeof property === 'string') record('walletErrors.get', [property])
      return Reflect.get(target, property, receiver)
    }
  })
  return { ...moduleObject, WalletError: Wrapped, default: Wrapped, walletErrors: enumView }
})
