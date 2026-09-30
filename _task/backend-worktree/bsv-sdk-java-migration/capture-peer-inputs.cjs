// 固定 Peer.test.ts 的 30 个原用例：Peer 构造、监听注册、会话发起、证书请求与响应、
// 入站消息与传输错误传播的真实入参（promise 结局由原断言核对）。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_AUTH_PEER_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Peer 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = testPath.slice(0, testPath.indexOf('/src/'))
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const callSite = new RegExp(sourceFile.split('/').pop().replace('.', '\\.') + ':(\\d+):\\d+')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let generation = 0
// 私钥十六进制 -> 产生它的代（0 表示 describe 作用域，早于任何用例）。
const drawnKeys = new Map()

function current () { return expect.getState().currentTestName }
// 只有原测试**直接**发起的调用才算公开入口：跳过探针自身的帧后，第一个带路径的
// 调用帧必须落在原测试文件里；Peer 内部自调用（帧在 Peer.ts）不记录。
function inTest () {
  const probe = path.basename(__filename)
  const target = sourceFile.split('/').pop()
  for (const line of String(new Error().stack).split('\n').slice(1)) {
    const match = line.match(/([^\s()]+):(\d+):(\d+)\)?$/)
    if (!match) continue
    const file = match[1]
    if (file.endsWith(probe)) continue
    return file.endsWith(target)
  }
  return false
}
function callLine () {
  const match = new Error().stack.match(callSite)
  return match ? Number(match[1]) : 0
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('Peer 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
// 钱包身份可复现时返回可比标签，否则返回 null（该次构造不作为入口样本）。
function walletLabel (wallet) {
  const root = wallet && wallet.keyDeriver ? wallet.keyDeriver.rootKey : undefined
  if (root === undefined || root === null) return null
  if (typeof root === 'string') return root
  if (typeof root.toArray !== 'function' || typeof root.toPublicKey !== 'function') return null
  const hex = Buffer.from(root.toArray()).toString('hex')
  const born = drawnKeys.get(hex)
  if (born !== undefined && born !== generation) return null
  return root.toPublicKey().toString()
}
const undefinedValue = { type: 'undefined' }
const ignored = { kind: 'return', value: { type: 'ignored' } }
function optional (value) { return value === undefined ? undefinedValue : value }
function describePolicy (policy) {
  if (policy === undefined) return undefinedValue
  return { certifiers: policy.certifiers, types: policy.types }
}
function describePayload (payload) {
  return Array.from(payload === undefined ? [] : payload, byte => byte & 0xff)
}
// 证书按可比字段描述：随机序列号、随机会话密钥加密的字段值与签名不参与比较，
// 字段名与 keyring 只比较名称。
function describeCertificate (certificate) {
  return { type: certificate.type, certifier: certificate.certifier, subject: certificate.subject,
    revocationOutpoint: certificate.revocationOutpoint === undefined ? undefinedValue
      : certificate.revocationOutpoint,
    fieldNames: certificate.fields === undefined ? undefinedValue : Object.keys(certificate.fields).sort(),
    keyringKeys: certificate.keyring === undefined ? [] : Object.keys(certificate.keyring).sort() }
}
function describeError (error) {
  if (error !== null && typeof error === 'object' && typeof error.message !== 'undefined') {
    return { kind: 'error', name: error.constructor ? error.constructor.name : 'Error', message: String(error.message) }
  }
  return { kind: 'value', value: error === undefined ? undefinedValue : String(error) }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  generation += 1
})

// Rand 经 globalThis.crypto.getRandomValues 取熵：32 字节的抽取登记为“本代产生的私钥”。
const originalCrypto = globalThis.crypto
const entropy = { subtle: originalCrypto && originalCrypto.subtle }
Object.defineProperty(entropy, 'getRandomValues', { value (array) {
  if (array.length === 32) {
    originalCrypto.getRandomValues(array)
    drawnKeys.set(Buffer.from(array).toString('hex'), generation)
    return array
  }
  return originalCrypto.getRandomValues(array)
} })
Object.defineProperty(globalThis, 'crypto', { configurable: true, value: entropy })

const modulePath = path.resolve(sdk, 'src/auth/Peer.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Original = actual.Peer
  return { ...actual, Peer: new Proxy(Original, {
    construct (target, args, newTarget) {
      const line = callLine()
      const instance = Reflect.construct(target, args, newTarget)
      if (!inTest()) return instance
      const label = walletLabel(args[0])
      if (label !== null) {
        record('constructor', [label, 'transport', describePolicy(args[2]),
          args[3] === undefined || args[3] === null ? undefinedValue : 'asyncStore'], null, line)
      }
      const wrap = (name, describeArgs) => {
        const original = instance[name].bind(instance)
        instance[name] = (...methodArgs) => {
          if (!inTest()) return original(...methodArgs)
          const at = callLine()
          let result, error
          try {
            result = original(...methodArgs)
          } catch (caught) {
            error = caught
          }
          record(name, describeArgs(methodArgs), error === undefined ? ignored : { kind: 'throw',
            name: error.constructor ? error.constructor.name : 'Error', message: String(error.message) }, at)
          if (error !== undefined) throw error
          return result
        }
      }
      wrap('listenForGeneralMessages', () => ['function'])
      wrap('listenForCertificatesReceived', () => ['function'])
      wrap('listenForCertificatesRequested', () => ['function'])
      wrap('stopListeningForGeneralMessages', methodArgs => [methodArgs[0]])
      wrap('toPeer', methodArgs => [describePayload(methodArgs[0]), optional(methodArgs[1])])
      wrap('requestCertificates', methodArgs => [describePolicy(methodArgs[0]), optional(methodArgs[1])])
      wrap('getAuthenticatedSession', methodArgs => [optional(methodArgs[0])])
      wrap('sendCertificateResponse', methodArgs =>
        [optional(methodArgs[0]), (methodArgs[1] === undefined ? [] : methodArgs[1]).map(describeCertificate)])
      wrap('handleIncomingMessage', methodArgs =>
        [methodArgs[0] === undefined ? undefinedValue : methodArgs[0]])
      wrap('propagateTransportError', methodArgs => [optional(methodArgs[0]), describeError(methodArgs[1])])
      return instance
    }
  }) }
})
