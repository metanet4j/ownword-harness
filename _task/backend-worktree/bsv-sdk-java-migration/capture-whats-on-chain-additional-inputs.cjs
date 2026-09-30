// 固定 WhatsOnChain.additional.test.ts 原输入：构造入参、注入 fetch／httpClient 的实际请求与实际响应、查询结局。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_WHATS_ON_CHAIN_ADDITIONAL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 WhatsOnChain.additional 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const whatsOnChainPath = path.join(sdk, 'src/transaction/chaintrackers/WhatsOnChain.ts')
const fetchHttpClientPath = path.join(sdk, 'src/transaction/http/FetchHttpClient.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/WhatsOnChain\.additional\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : 0
}
function inTestFile () { return /WhatsOnChain\.additional\.test\.ts:\d+:\d+/.test(new Error().stack) }
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('WhatsOnChain.additional 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

// 原测试注入的是 jest.fn()：保留 mock 身份与调用记录（原断言核对调用次数与调用参数），
// 只在其实现外面记录实际请求与实际响应。
const attached = new WeakSet()
function attachMock (client, key) {
  if (!client || !jest.isMockFunction(client[key])) return
  if (attached.has(client[key])) return
  attached.add(client[key])
  const original = client[key].getMockImplementation()
  client[key].mockImplementation(async (...args) => {
    try {
      const response = await (original ? original(...args) : undefined)
      const outcome = key === 'fetch' ? await describeFetchResponse(response) : describeRequestResponse(response)
      record(key, args, outcome)
      return response
    } catch (error) {
      record(key, args, { kind: 'reject', name: error && error.constructor ? error.constructor.name : 'Error',
        message: error instanceof Error ? error.message : String(error) })
      throw error
    }
  })
}

// 与 FetchHttpClient.request 的实际取值一致：content-type 决定 json／text。
async function describeFetchResponse (response) {
  const get = response && response.headers && typeof response.headers.get === 'function' ? response.headers.get('Content-Type') : null
  const contentType = get === undefined ? null : get
  const outcome = { kind: 'resolve', ok: !!response.ok, status: response.status ?? null,
    statusText: response.statusText ?? null, contentType }
  const isJson = contentType !== null && contentType.startsWith('application/json')
  const body = isJson ? await response.json() : (typeof response.text === 'function' ? await response.text() : undefined)
  if (body !== undefined) outcome.body = body
  return outcome
}

function describeRequestResponse (response) {
  const outcome = { kind: 'resolve', ok: !!response.ok, status: response.status ?? null,
    statusText: response.statusText ?? null }
  if ('data' in response) outcome.data = response.data
  return outcome
}

function attachClient (client) {
  if (!client) return
  if (jest.isMockFunction(client.fetch)) attachMock(client, 'fetch')
  else if (jest.isMockFunction(client.request)) attachMock(client, 'request')
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

// 原测试直接 new FetchHttpClient(mockFetch)：只在其 mock 外面记录真正的 fetch 入参与响应。
jest.doMock(fetchHttpClientPath, () => {
  const original = jest.requireActual(fetchHttpClientPath)
  const FetchHttpClient = new Proxy(original.FetchHttpClient, {
    construct (target, args, newTarget) {
      if (inTestFile()) attachMock(args[0], 'fetch')
      return Reflect.construct(target, args, newTarget)
    }
  })
  return { ...original, FetchHttpClient, __esModule: true }
})

jest.doMock(whatsOnChainPath, () => {
  const original = jest.requireActual(whatsOnChainPath)
  const WhatsOnChain = new Proxy(original.default, {
    construct (target, args, newTarget) {
      const config = args[1] || {}
      if (inTestFile()) {
        attachClient(config.httpClient)
        record('constructor', [{
          network: args[0],
          apiKey: config.apiKey === undefined ? null : config.apiKey,
          hasHttpClient: config.httpClient !== undefined && config.httpClient !== null
        }], null)
      }
      return wrapInstance(Reflect.construct(target, args, newTarget))
    }
  })
  return { ...original, default: WhatsOnChain, __esModule: true }
})
