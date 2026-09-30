// 固定 DefaultHttpClient.test.ts 原输入：环境可选分支、注入 fetch 的实际请求与实际响应。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_DEFAULT_HTTP_CLIENT_TS_OBSERVATIONS
if (!output) throw new Error('缺少 DefaultHttpClient 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const defaultHttpClientPath = path.join(sdk, 'src/transaction/http/DefaultHttpClient.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/DefaultHttpClient\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : 0
}
function inTestFile () { return /DefaultHttpClient\.test\.ts:\d+:\d+/.test(new Error().stack) }
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('DefaultHttpClient 入口发生在固定测试之外')
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

const attached = new WeakSet()
function attachMock (fetcher) {
  if (!fetcher || !jest.isMockFunction(fetcher)) return
  if (attached.has(fetcher)) return
  attached.add(fetcher)
  const original = fetcher.getMockImplementation()
  fetcher.mockImplementation(async (...args) => {
    try {
      const response = await (original ? original(...args) : undefined)
      const outcome = await describeFetchResponse(response)
      record('fetch', args, outcome)
      return response
    } catch (error) {
      record('fetch', args, { kind: 'reject',
        name: error && error.constructor ? error.constructor.name : 'Error',
        message: error instanceof Error ? error.message : String(error) })
      throw error
    }
  })
}

// 与 FetchHttpClient.request 的实际取值一致：content-type 决定 json／text。
async function describeFetchResponse (response) {
  const get = response && response.headers && typeof response.headers.get === 'function'
    ? response.headers.get('Content-Type') : null
  const contentType = get === undefined ? null : get
  const outcome = { kind: 'resolve', ok: !!response.ok, status: response.status ?? null,
    statusText: response.statusText ?? null, contentType }
  const isJson = contentType !== null && contentType.startsWith('application/json')
  const body = isJson ? await response.json() : (typeof response.text === 'function' ? await response.text() : undefined)
  if (body !== undefined) outcome.body = body
  return outcome
}

// 原测试把 jest.fn() 挂到 global.window.fetch 上：保留 mock 身份与调用记录，只在其实现外面
// 记录实际请求与实际响应。DefaultHttpClient 经 requireActual 载入，改 mock FetchHttpClient
// 模块对它无效，所以在 window 赋值处装记录器；原测试的 afterEach 会删掉 window，需每次重装。
let wrappedWindow
function installWindowAccessor () {
  Object.defineProperty(globalThis, 'window', {
    configurable: true,
    get () { return wrappedWindow },
    set (value) {
      if (value && jest.isMockFunction(value.fetch)) attachMock(value.fetch)
      wrappedWindow = value
    }
  })
}
installWindowAccessor()
beforeEach(installWindowAccessor)

jest.doMock(defaultHttpClientPath, () => {
  const original = jest.requireActual(defaultHttpClientPath)
  return { ...original, __esModule: true,
    defaultHttpClient: function (...args) {
      // 选择入口在返回客户端之前记录，保证两侧入口顺序一致。
      if (inTestFile()) record('defaultHttpClient', [environment()], null)
      return original.defaultHttpClient(...args)
    } }
})
