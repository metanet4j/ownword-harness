// 固定 WalletClient.substrate.test.ts 的原入口：转发给注入基底的每个公开调用实参。
// 该文件每条用例只 new 一次并调用一个方法，因此只包装原型方法，不登记构造。
// WalletClient 与基底互相引用，因此用真实模块且只安装一次。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_WALLET_CLIENT_SUBSTRATE_TS_OBSERVATIONS
if (!output) throw new Error('缺少 WalletClient.substrate 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/wallet/WalletClient.ts')
const methods = ['connectToSubstrate', 'relinquishOutput', 'getPublicKey', 'revealCounterpartyKeyLinkage',
  'revealSpecificKeyLinkage', 'encrypt', 'decrypt', 'createHmac', 'verifyHmac', 'createSignature',
  'verifySignature', 'acquireCertificate', 'listCertificates', 'proveCertificate',
  'relinquishCertificate', 'discoverByIdentityKey', 'discoverByAttributes', 'isAuthenticated',
  'waitForAuthentication', 'getHeight', 'getHeaderForHeight', 'getNetwork', 'getVersion',
  'createAction', 'signAction', 'abortAction', 'listActions', 'internalizeAction', 'listOutputs']
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/WalletClient\.substrate\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('WalletClient.substrate 入口缺少固定原测试调用位置')
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
  throw new Error('WalletClient.substrate 原输入暂不支持：' + typeof value)
}
function record (method, args, line = callLine()) {
  const test = current()
  if (!test) throw new Error('WalletClient.substrate 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args }) + '\n')
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  const Original = moduleObject.default
  for (const name of methods) {
    if (typeof Original.prototype[name] !== 'function') throw new Error('固定 WalletClient 方法不存在：' + name)
    const original = Original.prototype[name]
    Original.prototype[name] = function (...args) {
      // 转发方法内部会先调用 connectToSubstrate；只登记固定测试自己的入口。
      if (depth === 0) record(name, args.map(tagged))
      depth++
      try { return Reflect.apply(original, this, args) } finally { depth-- }
    }
  }
  return moduleObject
})
