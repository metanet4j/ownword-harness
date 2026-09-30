// 固定 DefaultHttpClient.additional.test.ts 原输入：环境可选分支（含 https 是否可用）、无客户端兜底的请求与结局。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_DEFAULT_HTTP_CLIENT_ADDITIONAL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 DefaultHttpClient.additional 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const defaultHttpClientPath = path.join(sdk, 'src/transaction/http/DefaultHttpClient.ts')
const binaryFetchClientPath = path.join(sdk, 'src/transaction/http/BinaryFetchClient.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/DefaultHttpClient\.additional\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : 0
}
function inTestFile () { return /DefaultHttpClient\.additional\.test\.ts:\d+:\d+/.test(new Error().stack) }
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('DefaultHttpClient.additional 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

// 只记录两侧都能一致镜像的可选分支：node:https 的可达性在固定测试里被 jest.mock('https')
// 跨用例残留（用例 3／6 实际也走兜底），记进来会和 Java 侧“https 可用”的原断言冲突。
function environment () {
  return {
    windowFetch: typeof globalThis.window !== 'undefined' && typeof globalThis.window.fetch === 'function',
    globalFetch: typeof globalThis.fetch === 'function'
  }
}

// 类型化数组按元素记录：JSON.stringify(Uint8Array) 给的是下标对象，跨语言不可比。
function normalize (value) {
  if (value instanceof Uint8Array || (typeof Buffer !== 'undefined' && Buffer.isBuffer(value))) {
    return Array.from(value, byte => byte & 0xff)
  }
  if (Array.isArray(value)) return value.map(normalize)
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, normalize(item)]))
  }
  return value
}

const wrappers = new WeakMap()
function wrapClient (client) {
  if (!client || typeof client.request !== 'function') return client
  if (wrappers.has(client)) return wrappers.get(client)
  const proxy = new Proxy(client, {
    get (target, property) {
      const value = Reflect.get(target, property, target)
      if (property !== 'request') return typeof value === 'function' ? value.bind(target) : value
      return async function (...args) {
        try {
          const response = await Reflect.apply(value, target, args)
          const outcome = { kind: 'resolve', ok: !!response.ok, status: response.status ?? null,
            statusText: response.statusText ?? null }
          if ('data' in response) outcome.data = response.data
          record('request', normalize(args), outcome)
          return response
        } catch (error) {
          record('request', normalize(args), { kind: 'reject',
            name: error && error.constructor ? error.constructor.name : 'Error',
            message: error instanceof Error ? error.message : String(error) })
          throw error
        }
      }
    }
  })
  wrappers.set(client, proxy)
  return proxy
}

jest.doMock(defaultHttpClientPath, () => {
  const original = jest.requireActual(defaultHttpClientPath)
  return { ...original, __esModule: true,
    defaultHttpClient: function (...args) {
      if (inTestFile()) record('defaultHttpClient', [environment()], null)
      return wrapClient(original.defaultHttpClient(...args))
    } }
})

jest.doMock(binaryFetchClientPath, () => {
  const original = jest.requireActual(binaryFetchClientPath)
  return { ...original, __esModule: true,
    binaryHttpClient: function (...args) {
      if (inTestFile()) record('binaryHttpClient', [environment()], null)
      return wrapClient(original.binaryHttpClient(...args))
    } }
})
