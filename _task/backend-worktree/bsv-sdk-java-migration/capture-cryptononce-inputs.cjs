// 固定 cryptononce.test.ts：逐例确定性熵流，以及 createNonce／verifyNonce 两个公开入口的
// 真实入参与结果（钱包按“固定 mock 钱包／真实钱包身份”可比描述）。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_AUTH_CRYPTONONCE_TS_OBSERVATIONS
if (!output) throw new Error('缺少 cryptononce 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = testPath.slice(0, testPath.indexOf('/src/'))
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const callSite = new RegExp(sourceFile.split('/').pop().replace('.', '\\.') + ':(\\d+):\\d+')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let randomState = 0x243f6a88

function current () { return expect.getState().currentTestName }
// 入口位置只在同步调用点可读；异步续体里栈已不含原测试帧，因此调用点先取行号。
function callLine () {
  const match = new Error().stack.match(callSite)
  return match ? Number(match[1]) : 0
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('cryptononce 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
// 固定 mock 钱包是对象字面量（没有 keyDeriver）；真实 CompletedProtoWallet 按身份公钥描述。
function walletLabel (wallet) {
  const root = wallet && wallet.keyDeriver ? wallet.keyDeriver.rootKey : undefined
  if (root === undefined || root === null) return 'mock'
  if (typeof root === 'string') return root
  return typeof root.toPublicKey === 'function' ? root.toPublicKey().toString() : 'mock'
}
function observed (method, args, promise, line) {
  return promise.then(
    value => { record(method, args, { kind: 'return', value }, line); return value },
    error => { record(method, args, thrown(error), line); throw error })
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  randomState = 0x243f6a88
})

// Rand 经 globalThis.crypto.getRandomValues 取熵：替换为固定 xorshift 流并逐次记录。
const originalCrypto = globalThis.crypto
const entropy = { subtle: originalCrypto && originalCrypto.subtle }
Object.defineProperty(entropy, 'getRandomValues', { value (array) {
  for (let index = 0; index < array.length; index++) {
    randomState ^= randomState << 13
    randomState ^= randomState >>> 17
    randomState ^= randomState << 5
    array[index] = randomState >>> 24
  }
  if (current()) record('random', [], { kind: 'entropy', length: array.length,
    bytesHex: Buffer.from(array).toString('hex') })
  return array
} })
Object.defineProperty(globalThis, 'crypto', { configurable: true, value: entropy })

function wrap (modulePath) {
  jest.doMock(modulePath, () => {
    const actual = jest.requireActual(modulePath)
    return {
      ...actual,
      createNonce: (wallet, counterparty, originator) => {
        const line = callLine()
        return observed('createNonce',
          [walletLabel(wallet), counterparty === undefined ? null : counterparty,
            originator === undefined ? null : originator],
          actual.createNonce(wallet, counterparty, originator), line)
      },
      verifyNonce: (nonce, wallet, counterparty, originator) => {
        const line = callLine()
        return observed('verifyNonce',
          [nonce, walletLabel(wallet), counterparty === undefined ? null : counterparty,
            originator === undefined ? null : originator],
          actual.verifyNonce(nonce, wallet, counterparty, originator), line)
      }
    }
  })
}

wrap(path.resolve(sdk, 'src/auth/utils/createNonce.ts'))
wrap(path.resolve(sdk, 'src/auth/utils/verifyNonce.ts'))
