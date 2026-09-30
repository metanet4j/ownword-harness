// 固定 WalletClient.additional.test.ts 的原入口：WalletClient 构造（基底别名）与各公开方法实参，
// 以及 WERR_INVALID_PARAMETER 类契约用例的构造入参。
// WalletClient 与基底互相引用，因此用真实模块只包装原型方法与构造函数，且每个模块只安装一次。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_WALLET_CLIENT_ADDITIONAL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 WalletClient.additional 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const clientPath = path.join(sdk, 'src/wallet/WalletClient.ts')
const errorPath = path.join(sdk, 'src/wallet/WERR_INVALID_PARAMETER.ts')
const methods = ['connectToSubstrate', 'createAction', 'signAction', 'abortAction', 'listActions',
  'listOutputs', 'relinquishOutput', 'acquireCertificate', 'listCertificates',
  'relinquishCertificate', 'discoverByIdentityKey', 'discoverByAttributes', 'proveCertificate']
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let clientInstalled = false
let errorInstalled = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/WalletClient\.additional\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('WalletClient.additional 入口缺少固定原测试调用位置')
  return Number(match[1])
}
function tagged (value) {
  if (value === undefined) return { type: 'undefined' }
  if (value === null) return { type: 'null' }
  if (typeof value === 'boolean') return { type: 'boolean', value }
  if (typeof value === 'string') return { type: 'string', value }
  if (typeof value === 'number') return { type: 'number', value: String(value) }
  if (value instanceof Uint8Array) {
    return { type: 'array', value: Array.from(value, item => ({ type: 'number', value: String(item & 0xff) })) }
  }
  if (Array.isArray(value)) return { type: 'array', value: value.map(tagged) }
  if (typeof value === 'object') {
    return { type: 'map', value: Object.fromEntries(Object.entries(value).map(([key, item]) => [key, tagged(item)])) }
  }
  throw new Error('WalletClient.additional 原输入暂不支持：' + typeof value)
}
// 构造入参只登记基底类别：预先构建的钱包对象无法逐值比较，字符串别名保留原值。
function substrateTag (value) {
  return typeof value === 'string' ? tagged(value) : { type: 'object' }
}
function record (method, args, line = callLine()) {
  const test = current()
  if (!test) throw new Error('WalletClient.additional 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args }) + '\n')
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(clientPath, () => {
  const moduleObject = jest.requireActual(clientPath)
  if (clientInstalled || moduleObject.default === undefined) return moduleObject
  clientInstalled = true
  const Original = moduleObject.default
  for (const name of methods) {
    if (typeof Original.prototype[name] !== 'function') throw new Error('固定 WalletClient 方法不存在：' + name)
    const original = Original.prototype[name]
    Original.prototype[name] = function (...args) {
      // 各公开方法内部会先调用 connectToSubstrate；只登记固定测试自己的入口。
      if (depth === 0) record(name, args.map(tagged))
      depth++
      try { return Reflect.apply(original, this, args) } finally { depth-- }
    }
  }
  const ProxyClass = new Proxy(Original, {
    construct (target, args, newTarget) {
      record('constructor', args.map(substrateTag))
      return Reflect.construct(target, args, newTarget)
    }
  })
  return { ...moduleObject, __esModule: true, default: ProxyClass }
})

jest.doMock(errorPath, () => {
  const moduleObject = jest.requireActual(errorPath)
  if (errorInstalled || moduleObject.default === undefined) return moduleObject
  errorInstalled = true
  const ProxyClass = new Proxy(moduleObject.default, {
    construct (target, args, newTarget) {
      // 校验失败时生产代码会抛出该错误；只登记固定测试自己构造的入口。
      if (depth === 0) record('constructor', args.map(tagged))
      return Reflect.construct(target, args, newTarget)
    }
  })
  return { ...moduleObject, __esModule: true, WERR_INVALID_PARAMETER: ProxyClass, default: ProxyClass }
})
