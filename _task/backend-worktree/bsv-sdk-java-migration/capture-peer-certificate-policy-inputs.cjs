// 固定 Peer.certificatePolicy.test.ts 的 15 个原用例：Peer 构造、监听注册、证书请求与
// 三类入站消息处理的真实入参（promise 结局不在入口样本内，由原断言核对）。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_AUTH_PEER_CERTIFICATE_POLICY_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Peer certificatePolicy 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = testPath.slice(0, testPath.indexOf('/src/'))
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const callSite = new RegExp(sourceFile.split('/').pop().replace('.', '\\.') + ':(\\d+):\\d+')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

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
  if (!test) throw new Error('Peer certificatePolicy 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name, message: error && error.message !== undefined ? String(error.message) : null }
}
const undefinedValue = { type: 'undefined' }
const ignored = { kind: 'return', value: { type: 'ignored' } }
function optional (value) { return value === undefined ? undefinedValue : value }
function describePolicy (policy) {
  if (policy === undefined) return undefinedValue
  return { certifiers: policy.certifiers, types: policy.types }
}
function describeCertificate (certificate) {
  return { type: certificate.type, certifier: certificate.certifier, subject: certificate.subject }
}
function describeMessage (message) {
  const out = { version: message.version, messageType: message.messageType, identityKey: message.identityKey,
    nonce: optional(message.nonce), initialNonce: optional(message.initialNonce),
    yourNonce: optional(message.yourNonce),
    certificates: (message.certificates === undefined ? [] : message.certificates).map(describeCertificate),
    signature: Array.from(message.signature === undefined ? [] : message.signature) }
  if (message.requestedCertificates !== undefined) {
    out.requestedCertificates = describePolicy(message.requestedCertificates)
  }
  return out
}
function describeSession (session) {
  if (session === undefined || session === null) return undefinedValue
  return { isAuthenticated: session.isAuthenticated, sessionNonce: optional(session.sessionNonce),
    peerNonce: optional(session.peerNonce), peerIdentityKey: optional(session.peerIdentityKey),
    lastUpdate: session.lastUpdate === undefined ? undefinedValue
      : { type: 'number', value: String(session.lastUpdate) },
    certificatesRequired: optional(session.certificatesRequired),
    certificatesValidated: optional(session.certificatesValidated) }
}
beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

const modulePath = path.resolve(sdk, 'src/auth/Peer.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Original = actual.Peer
  return { ...actual, Peer: new Proxy(Original, {
    construct (target, args, newTarget) {
      const instance = Reflect.construct(target, args, newTarget)
      if (!inTest()) return instance
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
          record(name, describeArgs(methodArgs), error === undefined ? ignored : thrown(error), at)
          if (error !== undefined) throw error
          return result
        }
      }
      wrap('listenForCertificatesReceived', () => ['function'])
      wrap('listenForGeneralMessages', () => ['function'])
      wrap('listenForCertificatesRequested', () => ['function'])
      wrap('requestCertificates', methodArgs => [describePolicy(methodArgs[0]), optional(methodArgs[1])])
      wrap('processCertificateResponse', methodArgs => [describeMessage(methodArgs[0])])
      wrap('processGeneralMessage', methodArgs => [describeMessage(methodArgs[0])])
      wrap('processCertificateRequest', methodArgs => [describeMessage(methodArgs[0])])
      wrap('validateInitialResponseCertificates', methodArgs =>
        [describeMessage(methodArgs[0]), describeSession(methodArgs[1])])
      wrap('updateCertificateSession', methodArgs => [methodArgs[0], 'function'])
      return instance
    }
  }) }
})
