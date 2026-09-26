// 固定 jsonByteEncoding.test.ts 的导出函数调用和 JSON replacer 的真实 holder。
'use strict'
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.MIGRATION_JSON_BYTE_TS_INPUTS
if (!output) throw new Error('缺少钱包 JSON 字节输入采集路径')
const sdk = path.resolve(path.dirname(expect.getState().testPath), '../../../..')
const modulePath = path.join(sdk, 'src/wallet/substrates/utils/jsonByteEncoding.ts')

function tagged(value) {
  if (value === undefined) return { type: 'undefined' }
  if (value === null) return { type: 'null' }
  if (typeof value === 'boolean') return { type: 'boolean', value }
  if (typeof value === 'string') return { type: 'string', value }
  if (typeof value === 'number') {
    const bits = Buffer.alloc(8)
    bits.writeDoubleBE(value)
    return { type: 'number', bits: bits.toString('hex') }
  }
  if (value instanceof Uint8Array) return { type: 'uint8array', bytes: Array.from(value) }
  if (Array.isArray(value)) return { type: 'array', value: value.map(tagged) }
  if (typeof value === 'object')
    return { type: 'object', entries: Object.entries(value).map(([key, item]) => ({ key, value: tagged(item) })) }
  throw new Error('固定钱包 JSON 字节测试含未支持入参类型：' + typeof value)
}

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  const wrapped = { ...moduleObject }
  for (const name of ['walletJsonReplacer', 'normalizeWalletJsonTx']) {
    const original = moduleObject[name]
    wrapped[name] = function (...args) {
      const test = expect.getState().currentTestName
      const location = new Error().stack.match(/\/jsonByteEncoding\.test\.ts:(\d+):\d+/)
      if (!test || !location) throw new Error('固定钱包 JSON 字节原测试调用位置缺失')
      const row = { test, line: Number(location[1]), method: name, args: args.map(tagged) }
      if (name === 'walletJsonReplacer') row.holder = tagged(this)
      fs.appendFileSync(output, JSON.stringify(row) + '\n')
      return Reflect.apply(original, this, args)
    }
  }
  return wrapped
})
