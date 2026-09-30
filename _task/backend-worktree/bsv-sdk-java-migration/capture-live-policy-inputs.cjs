// 固定 LivePolicy.test.ts 原输入：单例／构造入参、注入的 fetch 响应与结果、computeFee 入参和费用。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_LIVE_POLICY_TS_OBSERVATIONS
if (!output) throw new Error('缺少 LivePolicy 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/fee-models/LivePolicy.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/LivePolicy\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('LivePolicy 入口缺少固定原测试调用位置')
  return Number(match[1])
}
function inTestFile () {
  return /LivePolicy\.test\.ts:\d+:\d+/.test(new Error().stack)
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('LivePolicy 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence, source: { file: sourceFile, line },
    method, args, result }) + '\n')
}
// 原测试传的是 { inputs: [], outputs: [] } 的假交易，只记录可比的形状。
function describeTransaction (tx) {
  return { inputs: tx.inputs.length, outputs: tx.outputs.length }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

// 原测试在用例内替换 global.fetch；保留 mock 身份（原断言要核对调用次数），
// 只在其实现外面记录模块实际拿到的响应或拒绝。
let wrappedFetch = globalThis.fetch
Object.defineProperty(globalThis, 'fetch', {
  configurable: true,
  get () { return wrappedFetch },
  set (value) {
    if (jest.isMockFunction(value)) {
      const original = value.getMockImplementation()
      value.mockImplementation(async (...args) => {
        const url = String(args[0])
        try {
          const response = await (original ? original(...args) : undefined)
          const outcome = { kind: 'resolve', ok: response.ok, status: response.status ?? null,
            statusText: response.statusText ?? null }
          if (response.ok) outcome.body = await response.json()
          record('fetchResponse', [url], outcome)
          return response
        } catch (error) {
          record('fetchResponse', [url], { kind: 'reject', name: error.name, message: error.message })
          throw error
        }
      })
      wrappedFetch = value
      return
    }
    wrappedFetch = async (...args) => {
      const url = String(args[0])
      try {
        const response = await value(...args)
        const outcome = { kind: 'resolve', ok: response.ok, status: response.status ?? null,
          statusText: response.statusText ?? null }
        if (response.ok) outcome.body = await response.json()
        record('fetchResponse', [url], outcome)
        return response
      } catch (error) {
        record('fetchResponse', [url], { kind: 'reject', name: error.name, message: error.message })
        throw error
      }
    }
  }
})

const proxies = new WeakMap()
function wrapInstance (instance) {
  if (proxies.has(instance)) return proxies.get(instance)
  const proxy = new Proxy(instance, {
    get (target, property) {
      const value = Reflect.get(target, property, target)
      if (property === 'computeFee') {
        return async function (tx) {
          const descriptor = describeTransaction(tx)
          try {
            const fee = await Reflect.apply(value, target, [tx])
            record('computeFee', [descriptor], { kind: 'return', fee })
            return fee
          } catch (error) {
            record('computeFee', [descriptor], { kind: 'throw', name: error.constructor.name, message: error.message })
            throw error
          }
        }
      }
      return typeof value === 'function' ? value.bind(target) : value
    },
    set (target, property, value) {
      // 原测试用「当前时间减固定窗口」制造过期；按秒对齐，避免赋值与采集之间的毫秒抖动。
      if (property === 'cacheTimestamp') record('cacheTimestamp', [], { offsetMs: Math.round((Date.now() - value) / 1000) * 1000 })
      target[property] = value
      return true
    }
  })
  proxies.set(instance, proxy)
  return proxy
}

jest.doMock(modulePath, () => {
  const original = jest.requireActual(modulePath)
  const LivePolicy = new Proxy(original.default, {
    construct (target, args, newTarget) {
      // 只有原测试直接 new 才记入口；getInstance 内部的构造归到 getInstance。
      if (inTestFile()) record('constructor', args, null)
      return wrapInstance(Reflect.construct(target, args, newTarget))
    },
    get (target, property) {
      const value = Reflect.get(target, property, target)
      if (property === 'getInstance') {
        return function (...args) {
          const instance = Reflect.apply(value, target, args)
          record('getInstance', args, null)
          return wrapInstance(instance)
        }
      }
      return typeof value === 'function' ? value.bind(target) : value
    }
  })
  return { ...original, default: LivePolicy, __esModule: true }
})
