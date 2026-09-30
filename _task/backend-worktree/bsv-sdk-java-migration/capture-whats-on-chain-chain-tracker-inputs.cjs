// 固定 WhatsOnChainChainTracker.test.ts 原输入：默认客户端选择、构造入参、注入 httpClient 的实际请求与响应、查询结局。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_WHATS_ON_CHAIN_CHAIN_TRACKER_TS_OBSERVATIONS
if (!output) throw new Error('缺少 WhatsOnChainChainTracker 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const whatsOnChainPath = path.join(sdk, 'src/transaction/chaintrackers/WhatsOnChain.ts')
const defaultHttpClientPath = path.join(sdk, 'src/transaction/http/DefaultHttpClient.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/WhatsOnChainChainTracker\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : 0
}
function inTestFile () { return /WhatsOnChainChainTracker\.test\.ts:\d+:\d+/.test(new Error().stack) }
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('WhatsOnChainChainTracker 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

// 原测试注入的 httpClient 只有 request 一个入口：保留实例身份，只包住 request 记录实际请求与结局。
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
          record('request', args, outcome)
          return response
        } catch (error) {
          record('request', args, { kind: 'reject',
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

// 原测试不传 httpClient 时走 defaultHttpClient()：记录环境可以选择的分支，并包住选中的客户端。
jest.doMock(defaultHttpClientPath, () => {
  const original = jest.requireActual(defaultHttpClientPath)
  return { ...original, __esModule: true,
    defaultHttpClient: function (...args) {
      if (inTestFile()) {
        record('defaultHttpClient', [{
          windowFetch: typeof globalThis.window !== 'undefined' && typeof globalThis.window.fetch === 'function',
          globalFetch: typeof globalThis.fetch === 'function'
        }], null)
      }
      return wrapClient(original.defaultHttpClient(...args))
    } }
})

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

jest.doMock(whatsOnChainPath, () => {
  const original = jest.requireActual(whatsOnChainPath)
  const WhatsOnChain = new Proxy(original.default, {
    construct (target, args, newTarget) {
      const config = args[1] || {}
      const httpClient = config.httpClient
      const instance = Reflect.construct(target, httpClient === undefined || httpClient === null
        ? args : [args[0], { ...config, httpClient: wrapClient(httpClient) }], newTarget)
      // 默认选择发生在构造体内部：选择入口先记，构造入口后记，保证两侧入口顺序一致。
      if (inTestFile()) {
        record('constructor', [{ network: args[0],
          apiKey: config.apiKey === undefined ? null : config.apiKey,
          hasHttpClient: httpClient !== undefined && httpClient !== null }], null)
      }
      return wrapInstance(instance)
    }
  })
  return { ...original, default: WhatsOnChain, __esModule: true }
})
