// 固定 BRC100ByteEncoding.test.ts 的公开 API 入参与调用前状态；不修改原测试。
'use strict'
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.MIGRATION_BRC100_TS_INPUTS
if (!output) throw new Error('缺少 BRC-100 输入采集路径')
const sdk = path.resolve(path.dirname(expect.getState().testPath), '../../..')
const modulePath = path.join(sdk, 'src/wallet/BRC100ByteEncoding.ts')

function tagged(value, ancestors = new WeakSet()) {
  if (value === undefined) return { type: 'undefined' }
  if (value === null) return { type: 'null' }
  if (typeof value === 'boolean') return { type: 'boolean', value }
  if (typeof value === 'string') return { type: 'string', value }
  if (typeof value === 'symbol') return { type: 'symbol', description: value.description ?? null }
  if (typeof value === 'number') {
    const bits = Buffer.alloc(8)
    bits.writeDoubleBE(value)
    return { type: 'number', bits: bits.toString('hex') }
  }
  if (typeof value !== 'object') throw new Error('未支持的 BRC-100 入参类型：' + typeof value)
  if (ancestors.has(value)) return { type: 'cycle' }
  ancestors.add(value)
  try {
    if (Buffer.isBuffer(value)) return { type: 'buffer', bytes: Array.from(value) }
    if (ArrayBuffer.isView(value)) {
      const kind = Object.prototype.toString.call(value).slice(8, -1)
      const bytes = Array.from(new Uint8Array(value.buffer, value.byteOffset, value.byteLength))
      const ctor = Object.getPrototypeOf(value).constructor
      const realm = kind === 'Uint8Array' && ctor !== Uint8Array && ctor.name === 'Uint8Array'
        ? 'foreign' : 'local'
      return { type: 'view', kind, constructor: ctor.name, realm, bytes }
    }
    if (Object.prototype.toString.call(value) === '[object ArrayBuffer]')
      return { type: 'arrayBuffer', bytes: Array.from(new Uint8Array(value)) }
    if (Array.isArray(value)) {
      const entries = []
      for (let index = 0; index < value.length; index++)
        if (Object.hasOwn(value, index)) entries.push({ index, value: tagged(value[index], ancestors) })
      return { type: 'array', length: value.length, entries }
    }
    const descriptors = Object.getOwnPropertyDescriptors(value)
    const entries = []
    for (const [key, descriptor] of Object.entries(descriptors)) {
      if (!descriptor.enumerable) continue
      if (!Object.hasOwn(descriptor, 'value')) throw new Error('测试对象含访问器属性：' + key)
      entries.push({ key, value: tagged(descriptor.value, ancestors) })
    }
    const prototype = Object.getPrototypeOf(value)
    const inherited = []
    if (prototype !== Object.prototype && prototype !== null) {
      for (const key of Object.keys(prototype))
        inherited.push({ key, value: tagged(prototype[key], ancestors) })
    }
    return { type: 'object', entries, inherited, nullPrototype: prototype === null }
  } catch (error) {
    if (error.message === 'hostile ownKeys') return { type: 'hostile', trap: 'ownKeys', message: error.message }
    throw error
  } finally {
    ancestors.delete(value)
  }
}

const names = [
  'brc100JsonReplacer', 'normalizeBRC100ByteArray', 'normalizeBRC100ByteFields',
  'normalizeBRC100WalletByteFields', 'stringifyBRC100', 'toBRC100PortableByteArray'
]
jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  const wrapped = { ...moduleObject }
  for (const name of names) {
    const original = moduleObject[name]
    wrapped[name] = function (...args) {
      const test = expect.getState().currentTestName
      const location = new Error().stack.match(/\/BRC100ByteEncoding\.test\.ts:(\d+):\d+/)
      if (!test || !location) throw new Error('固定 BRC-100 原测试调用位置缺失')
      const row = { test, line: Number(location[1]), method: name, args: args.map(arg => tagged(arg)) }
      if (name === 'brc100JsonReplacer') row.holder = tagged(this)
      fs.appendFileSync(output, JSON.stringify(row) + '\n')
      return Reflect.apply(original, this, args)
    }
  }
  return wrapped
})
