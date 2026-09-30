// 固定 HTTPWalletJSON.test.ts 的构造、API 调用和 mock fetch 边界。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_HTTP_WALLET_JSON_TS_OBSERVATIONS
if (!output) throw new Error('缺少 HTTPWalletJSON 原输入采集路径')
const wireOutput = process.env.MIGRATION_HTTP_WALLET_JSON_TS_WIRE || output + '.wire.jsonl'
const sdk = path.resolve(path.dirname(expect.getState().testPath), '../../../..')
const modulePath = path.join(sdk, 'src/wallet/substrates/HTTPWalletJSON.ts')
const file = 'src/wallet/substrates/__tests/HTTPWalletJSON.test.ts'
const occurrenceByTest = new Map()
const sequenceByTest = new Map()
let occurrence = 0
let clients = []

function current () { return expect.getState().currentTestName }
function sourceLine () {
  const location = new Error().stack.match(/\/HTTPWalletJSON\.test\.ts:(\d+):\d+/)
  if (!location) throw new Error('HTTPWalletJSON 入口缺少固定原测试调用站点')
  return Number(location[1])
}
function tag (value, seen = new Map()) {
  if (value === undefined) return { kind: 'Undefined' }
  if (value === null) return { kind: 'Null' }
  if (typeof value === 'string') return { kind: 'String', value }
  if (typeof value === 'boolean') return { kind: 'Boolean', value }
  if (typeof value === 'number') return { kind: 'Number', value: String(value) }
  if (typeof value === 'function') {
    if (!jest.isMockFunction(value)) throw new Error('HTTPWalletJSON 收到未支持的函数输入')
    return { kind: 'JestMock', source: String(value) }
  }
  if (value instanceof Uint8Array) return { kind: 'Uint8Array', bytesHex: Buffer.from(value).toString('hex') }
  if (Array.isArray(value)) {
    if (seen.has(value)) return { kind: 'Ref', id: seen.get(value) }
    const id = seen.size + 1; seen.set(value, id)
    return { kind: 'Array', id, value: value.map(item => tag(item, seen)) }
  }
  if (typeof value === 'object') {
    if (seen.has(value)) return { kind: 'Ref', id: seen.get(value) }
    const id = seen.size + 1; seen.set(value, id)
    const entries = {}
    for (const key of Object.keys(value).sort()) entries[key] = tag(value[key], seen)
    return { kind: 'Object', id, entries }
  }
  throw new Error('HTTPWalletJSON 原输入暂不支持：' + typeof value)
}
function record (method, args, line = sourceLine()) {
  const test = current()
  if (!test) throw new Error('HTTPWalletJSON 入口发生在固定测试之外')
  const key = test + '\0' + occurrence
  const sequence = (sequenceByTest.get(key) || 0) + 1
  sequenceByTest.set(key, sequence)
  const row = { test, occurrence, sequence, source: { file, line },
    className: 'HTTPWalletJSON', method, args: args.map(arg => tag(arg)),
    preState: { windowType: typeof globalThis.window, documentType: typeof globalThis.document,
      priorEvents: sequence - 1 } }
  fs.appendFileSync(output, JSON.stringify(row) + '\n')
  return row
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrenceByTest.get(test) || 0) + 1
  occurrenceByTest.set(test, occurrence)
  clients = []
})

afterEach(async () => {
  for (const client of clients) {
    const mock = client.fetch
    if (!mock || !jest.isMockFunction(mock)) continue
    for (let index = 0; index < mock.mock.calls.length; index++) {
      const site = client.apiSites[index]
      if (!site) throw new Error('HTTPWalletJSON fetch 调用没有对应的公开 API 入口')
      const [url, init] = mock.mock.calls[index]
      if (typeof init.body !== 'string') throw new Error('HTTPWalletJSON 固定请求体不是 JSON 字符串')
      const request = record('fetchRequest', [url, { ...init, body: JSON.parse(init.body) }], site)
      fs.appendFileSync(wireOutput, JSON.stringify({ test: request.test, occurrence: request.occurrence,
        sequence: request.sequence, url, rawBody: init.body }) + '\n')
      const result = mock.mock.results[index]
      if (result.type === 'throw') {
        record('fetchReject', [{ name: result.value.name, message: result.value.message }], site)
        continue
      }
      try {
        const response = await result.value
        record('fetchResponse', [{ ok: response.ok, status: response.status,
          body: await response.json() }], site)
      } catch (error) {
        record('fetchReject', [{ name: error.name, message: error.message }], site)
      }
    }
  }
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  const Original = moduleObject.default
  const ProxyClass = new Proxy(Original, {
    construct (target, args, newTarget) {
      record('constructor', args)
      const instance = Reflect.construct(target, args, newTarget)
      const observation = { fetch: args[2], apiSites: [] }
      clients.push(observation)
      const api = instance.api
      instance.api = function (...apiArgs) {
        const site = sourceLine()
        record('api', apiArgs, site)
        observation.apiSites.push(site)
        return Reflect.apply(api, this, apiArgs)
      }
      return instance
    }
  })
  return { ...moduleObject, __esModule: true, default: ProxyClass }
})
