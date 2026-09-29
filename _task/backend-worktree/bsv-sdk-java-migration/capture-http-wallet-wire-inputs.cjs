// 固定 HTTPWalletWire.test.ts 原输入：构造状态、公开传输入口与 mock fetch 边界的请求／响应。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_HTTP_WALLET_WIRE_TS_OBSERVATIONS
if (!output) throw new Error('缺少 HTTPWalletWire 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/wallet/substrates/HTTPWalletWire.ts')
const occurrences = new Map()
const sequenceByTest = new Map()
const wrappedClients = new WeakSet()
let occurrence = 0
let depth = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  // 异步回调里栈已不含原测试帧；行号只作说明，样本身份用入口名与序号。
  const match = new Error().stack.match(/HTTPWalletWire\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('HTTPWalletWire 入口发生在固定测试之外')
  const key = test + '\0' + occurrence
  const seq = (sequenceByTest.get(key) || 0) + 1
  sequenceByTest.set(key, seq)
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: seq,
    source: { file: sourceFile, line }, method, args: args.map(arg => tag(arg)), result }) + '\n')
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function tag (value) {
  if (value === undefined) return { kind: 'Undefined' }
  if (value === null) return { kind: 'Null' }
  if (typeof value === 'string') return { kind: 'String', value }
  if (typeof value === 'boolean') return { kind: 'Boolean', value }
  if (typeof value === 'number') return { kind: 'Number', value: String(value) }
  if (typeof value === 'function') {
    if (!jest.isMockFunction(value)) throw new Error('HTTPWalletWire 收到未支持的函数输入')
    return { kind: 'JestMock', source: String(value) }
  }
  if (value instanceof Uint8Array) return { kind: 'Uint8Array', bytesHex: hex(value) }
  if (Array.isArray(value)) return { kind: 'Array', value: value.map(item => tag(item)) }
  if (typeof value === 'object') {
    const entries = {}
    for (const key of Object.keys(value).sort()) entries[key] = tag(value[key])
    return { kind: 'Object', entries }
  }
  throw new Error('HTTPWalletWire 原输入暂不支持：' + typeof value)
}
// 保留 jest mock 身份（原断言核对调用次数与实参），只在实现外记录模块真正发出的请求与收到的响应。
function wrapClient (client) {
  if (!client || !jest.isMockFunction(client) || wrappedClients.has(client)) return
  wrappedClients.add(client)
  const original = client.getMockImplementation()
  client.mockImplementation(async function (...args) {
    const line = callLine()
    const [url, init] = args
    const request = { method: init?.method ?? null, headers: init?.headers ?? null, body: init?.body ?? null }
    try {
      const response = await Reflect.apply(original, this, args)
      const bytes = new Uint8Array(await response.arrayBuffer())
      record('fetch', [url, request], { kind: 'resolve', bytesHex: hex(bytes) }, line)
      return response
    } catch (error) {
      record('fetch', [url, request], { kind: 'reject', name: error.name, message: error.message ?? null }, line)
      throw error
    }
  })
}
function wrapTransmit (instance) {
  for (const name of ['transmitToWallet', 'transmitToWalletUint8Array']) {
    const original = instance[name].bind(instance)
    instance[name] = function (...args) {
      if (depth !== 0) return Reflect.apply(original, this, args)
      depth++
      const line = callLine()
      const promise = Promise.resolve(Reflect.apply(original, this, args))
      return promise.then(
        value => { depth--; record(name, args, tag(value), line); return value },
        error => { depth--; record(name, args, thrown(error), line); throw error })
    }
  }
}

const existing = Object.getOwnPropertyDescriptor(globalThis, 'fetch')
if (!existing || existing.configurable) {
  let currentFetch = globalThis.fetch
  Object.defineProperty(globalThis, 'fetch', { configurable: true, enumerable: true,
    get () { return currentFetch },
    set (value) { currentFetch = value; wrapClient(value) } })
} else throw new Error('HTTPWalletWire 原 fetch 属性不可观察')

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  const Original = moduleObject.default
  const ProxyClass = new Proxy(Original, {
    construct (target, args, newTarget) {
      const instance = Reflect.construct(target, args, newTarget)
      wrapClient(args[2] ?? globalThis.fetch)
      record('constructor', [instance.originator, instance.baseUrl], null)
      wrapTransmit(instance)
      return instance
    }
  })
  return { ...moduleObject, __esModule: true, default: ProxyClass }
})
