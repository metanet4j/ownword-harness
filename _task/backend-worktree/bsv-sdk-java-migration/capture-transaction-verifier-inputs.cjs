// 固定 Transaction.verifier.test.ts 原输入：随机私钥材料（buildValidTx 每次都新建私钥）、
// tx.verify 的后端与参数形状及最终结果，以及 verifyTransactionFee 的显式 undefined 守卫入参。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_TRANSACTION_VERIFIER_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Transaction verifier 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const privateKeyPath = path.join(sdk, 'src/primitives/PrivateKey.ts')
const transactionPath = path.join(sdk, 'src/transaction/Transaction.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let keyInstalled = false
let transactionInstalled = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/Transaction\.verifier\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('Transaction verifier 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function keyDescriptor (key) {
  return { hex: key.toHex(), wif: key.toWif(), publicKey: hex(Uint8Array.from(key.toPublicKey().encode(true))) }
}
function verifyArgsDescriptor (args) {
  return { scope: typeof args[0] === 'string' ? args[0] : '[object Object]',
    memoryLimit: args[2] === undefined ? null : args[2],
    hasFeeModel: args[1] !== undefined, hasVerifier: args[3] !== undefined }
}
function feeArgsDescriptor (args) {
  return { hasTx: args[0] !== undefined, hasFeeModel: args[1] !== undefined, hasTxid: typeof args[2] === 'function' }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  depth = 0
})

jest.doMock(privateKeyPath, () => {
  const moduleObject = jest.requireActual(privateKeyPath)
  if (keyInstalled || moduleObject.default === undefined) return moduleObject
  keyInstalled = true
  const Original = moduleObject.default
  const fromRandomOriginal = Original.fromRandom
  Original.fromRandom = function (...args) {
    const key = Reflect.apply(fromRandomOriginal, this, args)
    if (/Transaction\.verifier\.test\.ts:\d+:\d+/.test(new Error().stack)) record('fromRandom', [], keyDescriptor(key))
    return key
  }
  return moduleObject
})

jest.doMock(transactionPath, () => {
  const moduleObject = jest.requireActual(transactionPath)
  if (transactionInstalled || moduleObject.default === undefined) return moduleObject
  transactionInstalled = true
  const Original = moduleObject.default
  const verifyOriginal = Original.prototype.verify
  const feeOriginal = Original.prototype.verifyTransactionFee
  Original.prototype.verify = function (...args) {
    if (depth !== 0) return Reflect.apply(verifyOriginal, this, args)
    depth++
    const descriptor = verifyArgsDescriptor(args)
    return Promise.resolve(Reflect.apply(verifyOriginal, this, args)).then(
      value => { try { record('verify', [descriptor], { kind: 'return', value }) ; return value } finally { depth-- } },
      error => { try { record('verify', [descriptor], thrown(error)); throw error } finally { depth-- } }
    )
  }
  Original.prototype.verifyTransactionFee = function (...args) {
    if (depth !== 0) return Reflect.apply(feeOriginal, this, args)
    depth++
    const descriptor = feeArgsDescriptor(args)
    return Promise.resolve(Reflect.apply(feeOriginal, this, args)).then(
      value => { try { record('verifyTransactionFee', [descriptor], { kind: 'return' }); return value } finally { depth-- } },
      error => { try { record('verifyTransactionFee', [descriptor], thrown(error)); throw error } finally { depth-- } }
    )
  }
  return moduleObject
})
