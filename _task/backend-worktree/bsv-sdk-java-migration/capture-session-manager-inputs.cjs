// 固定 SessionManager.test.ts 的 11 个原用例：真实构造的管理器与五个公开入口的实际
// 入参和结果（会话按固定字段描述，区分 undefined 与 null）。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_AUTH_SESSION_MANAGER_TS_OBSERVATIONS
if (!output) throw new Error('缺少 SessionManager 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = testPath.slice(0, testPath.indexOf('/src/'))
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const callSite = new RegExp(sourceFile.split('/').pop().replace('.', '\\.') + ':(\\d+):\\d+')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(callSite)
  return match ? Number(match[1]) : 0
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('SessionManager 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
const undefinedValue = { type: 'undefined' }
function optional (value) {
  return value === undefined ? undefinedValue : value === null ? { type: 'null' } : value
}
// 固定原测试只使用这四个字段；null 在 Java 侧对应 undefined。
function describeSession (session) {
  return { isAuthenticated: session.isAuthenticated,
    sessionNonce: optional(session.sessionNonce), peerIdentityKey: optional(session.peerIdentityKey),
    lastUpdate: session.lastUpdate === undefined ? undefinedValue
      : { type: 'number', value: String(session.lastUpdate) } }
}
function isSession (value) {
  return value !== null && typeof value === 'object' && Object.hasOwn(value, 'isAuthenticated')
}
function describeArgument (value) {
  if (isSession(value)) return describeSession(value)
  return { type: 'string', value: String(value) }
}
function describeResult (value) {
  if (isSession(value)) return describeSession(value)
  if (value === undefined) return undefinedValue
  if (typeof value === 'boolean') return { type: 'boolean', value }
  return { type: 'string', value: String(value) }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

const modulePath = path.resolve(sdk, 'src/auth/SessionManager.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Original = actual.SessionManager
  function wrap (instance, name) {
    const original = instance[name].bind(instance)
    instance[name] = (...args) => {
      const line = callLine()
      let result, error
      try {
        result = original(...args)
      } catch (caught) {
        error = caught
      }
      record(name, args.map(describeArgument), error === undefined
        ? { kind: 'return', value: describeResult(result) } : thrown(error), line)
      if (error !== undefined) throw error
      return result
    }
  }
  return { ...actual, SessionManager: new Proxy(Original, {
    construct (target, args, newTarget) {
      const line = callLine()
      const instance = Reflect.construct(target, args, newTarget)
      for (const name of ['addSession', 'updateSession', 'getSession', 'removeSession', 'hasSession']) {
        wrap(instance, name)
      }
      record('constructor', [], { kind: 'return', value: { type: 'SessionManager' } }, line)
      return instance
    }
  }) }
})
