// 固定 SimplifiedFetchTransport.test.ts 的三个原用例：真实构造的传输实例、每次 send 交给
// 注入 fetch client 的 url/请求，以及 send 观察到的消息与结果（未发生时如实记为 null）。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_AUTH_SIMPLIFIED_FETCH_TRANSPORT_TS_OBSERVATIONS
if (!output) throw new Error('缺少 SimplifiedFetchTransport 原输入采集路径')
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
  if (!test) throw new Error('SimplifiedFetchTransport 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name, message: error && error.message !== undefined ? String(error.message) : null }
}
// 请求头名在 HTTP 语义下不区分大小写；统一小写，两侧构造顺序一致。
function describeHeaders (headers) {
  return Object.entries(headers).map(([key, value]) => [String(key).toLowerCase(), String(value)])
}
function describeBody (body) {
  if (body === undefined) return { type: 'undefined' }
  if (body === null) return { type: 'null' }
  if (typeof body === 'string') return { type: 'string', value: body }
  if (body instanceof Uint8Array) return { type: 'array', value: Array.from(body, byte => byte & 0xff) }
  return { type: 'string', value: String(body) }
}
function describeOptions (options) {
  return { method: options && options.method !== undefined ? String(options.method) : null,
    headers: describeHeaders(options && options.headers ? options.headers : {}),
    body: describeBody(options ? options.body : undefined) }
}
function describeMessage (message) {
  return { version: message.version, messageType: message.messageType, identityKey: message.identityKey,
    nonce: message.nonce === undefined ? { type: 'undefined' } : message.nonce,
    yourNonce: message.yourNonce === undefined ? { type: 'undefined' } : message.yourNonce,
    payload: Array.from(message.payload ?? [], byte => byte & 0xff),
    signature: Array.from(message.signature ?? [], byte => byte & 0xff) }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

const modulePath = path.resolve(sdk, 'src/auth/transports/SimplifiedFetchTransport.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Original = actual.SimplifiedFetchTransport
  return { ...actual, SimplifiedFetchTransport: new Proxy(Original, {
    construct (target, args, newTarget) {
      const line = callLine()
      const described = [String(args[0]), typeof args[1] === 'function' ? args[1].name || 'function' : null]
      const instance = Reflect.construct(target, args, newTarget)
      record('constructor', described, null, line)
      const fetchClient = instance.fetchClient
      if (typeof fetchClient !== 'function') return instance
      const send = instance.send.bind(instance)
      // 只在 send 期间替换 fetchClient，保证 `transport.fetchClient` 的原始身份可被原断言核对。
      instance.send = async function (message) {
        let captured = null
        instance.fetchClient = function (url, options) {
          if (captured === null) captured = [String(url), describeOptions(options)]
          return Reflect.apply(fetchClient, undefined, [url, options])
        }
        try {
          const result = await send(message)
          record('send', [describeMessage(message), captured, { kind: 'return' }], null, line)
          return result
        } catch (error) {
          record('send', [describeMessage(message), captured, thrown(error)], null, line)
          throw error
        } finally {
          instance.fetchClient = fetchClient
        }
      }
      return instance
    }
  }) }
})
