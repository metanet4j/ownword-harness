// 固定 Peer.boundary.test.ts 的两个原用例：Peer 构造、未关联会话等待者、会话发起与
// 按 nonce 停止等待的真实入参和结果。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_AUTH_PEER_BOUNDARY_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Peer boundary 原输入采集路径')
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
  if (!test) throw new Error('Peer boundary 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
// 只用于“调用本身没有同步抛错”的入口（返回的 promise 不在本例断言范围内）。
const ignored = { type: 'ignored' }
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
})

const modulePath = path.resolve(sdk, 'src/auth/Peer.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Original = actual.Peer
  return { ...actual, Peer: new Proxy(Original, {
    construct (target, args, newTarget) {
      const line = callLine()
      const instance = Reflect.construct(target, args, newTarget)
      if (!inTest()) return instance
      record('constructor', [walletLabel(args[0]), 'transport'], null, line)
      const wait = instance.waitForInitialResponse.bind(instance)
      instance.waitForInitialResponse = nonce => {
        if (!inTest()) return wait(nonce)
        const at = callLine()
        let result, error
        try {
          result = wait(nonce)
        } catch (caught) {
          error = caught
        }
        record('waitForInitialResponse', [nonce], error === undefined
          ? { kind: 'return', value: ignored } : thrown(error), at)
        if (error !== undefined) throw error
        return result
      }
      const stop = instance.stopListeningForInitialResponsesByNonce.bind(instance)
      instance.stopListeningForInitialResponsesByNonce = nonce => {
        if (!inTest()) return stop(nonce)
        const at = callLine()
        stop(nonce)
        record('stopListeningForInitialResponsesByNonce', [nonce],
          { kind: 'return', value: ignored }, at)
      }
      const authenticate = instance.getAuthenticatedSession.bind(instance)
      instance.getAuthenticatedSession = identityKey => {
        if (!inTest()) return authenticate(identityKey)
        const at = callLine()
        return observed('getAuthenticatedSession', [identityKey === undefined ? null : identityKey],
          authenticate(identityKey), at)
      }
      return instance
    }
  }) }
})
