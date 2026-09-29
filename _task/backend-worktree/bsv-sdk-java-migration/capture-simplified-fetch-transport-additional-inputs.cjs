// 固定 SimplifiedFetchTransport.additional.test.ts 原输入：真实构造的传输实例，
// 以及每次 send 实际交给注入 fetch client 的 url/请求（未发生 fetch 时如实记为 null）。
// 传输类只包装构造函数，且只安装一次，避免工厂重入时拿到半初始化模块。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_SIMPLIFIED_FETCH_TRANSPORT_ADDITIONAL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 SimplifiedFetchTransport additional 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/auth/transports/SimplifiedFetchTransport.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let installed = false
// deserializeRequestPayload 的入口保护：只记直接调用，send 内部的同类调用不算独立入口。
let probing = false
let sending = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/SimplifiedFetchTransport\.additional\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('SimplifiedFetchTransport 入口缺少固定原测试调用位置')
  return Number(match[1])
}
function record (method, args, result, line) {
  const test = current()
  if (!test) throw new Error('SimplifiedFetchTransport 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
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
// 原测试直接调用的解析入口：method／urlPostfix／headers 逐值比较，body 按原始字节比较。
function describeDeserialized (result) {
  const out = { method: result.method, urlPostfix: result.urlPostfix, headers: result.headers }
  if (result.body === undefined) out.body = { type: 'undefined' }
  else out.body = { type: 'array', value: Array.from(result.body, byte => byte & 0xff) }
  out.requestId = result.requestId
  return out
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function install (Original) {
  // deserializeRequestPayload 只在原测试直接调用时记录；send 内部的同类调用不算独立入口。
  const deserializeOriginal = Original.prototype.deserializeRequestPayload
  Original.prototype.deserializeRequestPayload = function (...args) {
    if (probing || sending) return Reflect.apply(deserializeOriginal, this, args)
    probing = true
    const line = callLine()
    let result
    try {
      result = Reflect.apply(deserializeOriginal, this, args)
    } finally {
      probing = false
    }
    record('deserializeRequestPayload', [Array.from(args[0], byte => byte & 0xff)],
      { kind: 'return', value: describeDeserialized(result) }, line)
    return result
  }
  return new Proxy(Original, {
    construct (target, args, newTarget) {
      const line = callLine()
      const described = [String(args[0]),
        typeof args[1] === 'function' ? args[1].name || 'function' : null]
      let instance
      try {
        instance = Reflect.construct(target, args, newTarget)
      } catch (error) {
        // 构造被拒绝也要留下入口样本，否则该原用例没有可冻结输入。
        record('constructor', described, thrown(error), line)
        throw error
      }
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
        sending = true
        try {
          const result = await send(message)
          record('send', [captured, { kind: 'return' }], null, line)
          return result
        } catch (error) {
          record('send', [captured, thrown(error)], null, line)
          throw error
        } finally {
          sending = false
          instance.fetchClient = fetchClient
        }
      }
      return instance
    }
  })
}

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.SimplifiedFetchTransport === undefined) return moduleObject
  installed = true
  const SimplifiedFetchTransport = install(moduleObject.SimplifiedFetchTransport)
  return Object.assign({}, moduleObject, {
    SimplifiedFetchTransport, __esModule: true
  })
})
