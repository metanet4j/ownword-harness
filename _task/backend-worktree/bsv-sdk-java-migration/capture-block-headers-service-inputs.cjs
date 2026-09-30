// 固定 BlockHeadersService.test.ts 原输入：构造入参、注入 httpClient 的实际请求与实际响应、查询结局。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_BLOCK_HEADERS_SERVICE_TS_OBSERVATIONS
if (!output) throw new Error('缺少 BlockHeadersService 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/chaintrackers/BlockHeadersService.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/BlockHeadersService\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : 0
}
function inTestFile () { return /BlockHeadersService\.test\.ts:\d+:\d+/.test(new Error().stack) }
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('BlockHeadersService 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

// 原测试注入的 httpClient 就是 { request: jest.fn() }：保留 mock 身份与调用记录
// （原断言核对调用次数和调用参数），只在其实现外面记录实际请求与实际响应。
const attached = new WeakSet()
function attachRecorder (client) {
  if (!client || typeof client.request !== 'function' || !jest.isMockFunction(client.request)) return
  if (attached.has(client.request)) return
  attached.add(client.request)
  const original = client.request.getMockImplementation()
  client.request.mockImplementation(async (...args) => {
    try {
      const response = await (original ? original(...args) : undefined)
      const outcome = { kind: 'resolve', ok: !!response.ok, status: response.status ?? null,
        statusText: response.statusText ?? null }
      if ('data' in response) outcome.data = response.data
      record('request', args, outcome)
      return response
    } catch (error) {
      record('request', args, { kind: 'reject', name: error.constructor.name, message: error.message })
      throw error
    }
  })
}

const proxies = new WeakMap()
function wrapInstance (instance) {
  if (proxies.has(instance)) return proxies.get(instance)
  const proxy = new Proxy(instance, {
    get (target, property) {
      const value = Reflect.get(target, property, target)
      if (property === 'isValidRootForHeight' || property === 'currentHeight') {
        return function (...args) {
          return Promise.resolve(Reflect.apply(value, target, args)).then(
            result => { record(property, args, { kind: 'return', value: result }); return result },
            error => {
              record(property, args, { kind: 'throw', name: error.constructor.name, message: error.message })
              throw error
            })
        }
      }
      return typeof value === 'function' ? value.bind(target) : value
    }
  })
  proxies.set(instance, proxy)
  return proxy
}

jest.doMock(modulePath, () => {
  const original = jest.requireActual(modulePath)
  const BlockHeadersService = new Proxy(original.BlockHeadersService, {
    construct (target, args, newTarget) {
      const config = args[1] || {}
      if (inTestFile()) {
        if (config.httpClient) attachRecorder(config.httpClient)
        record('constructor', [{
          baseUrl: args[0],
          apiKey: config.apiKey === undefined ? null : config.apiKey,
          hasHttpClient: config.httpClient !== undefined && config.httpClient !== null
        }], null)
      }
      return wrapInstance(Reflect.construct(target, args, newTarget))
    }
  })
  return { ...original, BlockHeadersService, __esModule: true }
})
