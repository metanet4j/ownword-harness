// 固定 BinaryFetchClient.test.ts 原输入：注入的 mock 客户端收到的请求（url/options）与返回的响应，
// 以及 binaryHttpClient() 依据运行环境选出的客户端。原测试自身 mock 掉 executeNodejsRequest，
// 探针只包装真实模块的公开入口，不触发任何真实网络调用。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_BINARY_FETCH_CLIENT_TS_OBSERVATIONS
if (!output) throw new Error('缺少 BinaryFetchClient 原输入采集路径')
const testPath = expect.getState().testPath
// 原测试比 src/<module>/__tests 深一层（src/transaction/http/__tests），按 src 段定位 SDK 根。
const segments = testPath.split(path.sep)
const sdk = segments.slice(0, segments.lastIndexOf('src')).join(path.sep)
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/http/BinaryFetchClient.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  // 异步回调里栈已经不含原测试帧；行号只作说明，样本身份用入口名与序号。
  const match = new Error().stack.match(/BinaryFetchClient\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('BinaryFetchClient 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function observe (method, args, action, describe) {
  if (depth !== 0) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? null : describe(result))
    return result
  } catch (error) {
    record(method, args, thrown(error))
    throw error
  } finally {
    depth--
  }
}
// 异步入口：在 Promise 落定时写入实际返回或异常；请求参数在调用点先固定。
function observeAsync (method, args, action, describe) {
  const line = callLine()
  return Promise.resolve(action()).then(result => {
    record(method, args, describe === undefined ? null : describe(result), line)
    return result
  }, error => {
    record(method, args, thrown(error), line)
    throw error
  })
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function describeBytes (value) {
  if (value === undefined || value === null) return null
  if (typeof value === 'string') return { kind: 'string', value }
  if (value instanceof Uint8Array || Buffer.isBuffer(value)) return { kind: 'bytes', hex: hex(value) }
  return { kind: 'string', value: String(value) }
}
function describeOptions (options) {
  return { kind: 'requestOptions',
    method: options.method === undefined ? null : options.method,
    headers: options.headers === undefined || options.headers === null ? null : Object.fromEntries(Object.entries(options.headers)),
    data: describeBytes(options.data) }
}
function describeResponse (response) {
  return { kind: 'response', ok: response.ok, status: response.status,
    statusText: response.statusText, data: describeBytes(response.data) }
}
function describeClient (client) {
  return { kind: 'httpClient', hasRequest: typeof client.request === 'function' }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function install (moduleObject) {
  for (const name of ['BinaryFetchClient', 'BinaryNodejsHttpClient']) {
    const Original = moduleObject[name]
    const request = Original.prototype.request
    Original.prototype.request = function (...values) {
      return observeAsync('request', [values[0], describeOptions(values[1])],
        () => Reflect.apply(request, this, values), describeResponse)
    }
  }
  const binaryHttpClient = moduleObject.binaryHttpClient
  moduleObject.binaryHttpClient = function (...values) {
    return observe('binaryHttpClient', [],
      () => Reflect.apply(binaryHttpClient, this, values), describeClient)
  }
}

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.BinaryFetchClient === undefined) return moduleObject
  installed = true
  install(moduleObject)
  return moduleObject
})
