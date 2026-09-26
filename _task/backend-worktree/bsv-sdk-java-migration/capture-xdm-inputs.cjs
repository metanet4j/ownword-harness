// 固定 XDM.test.ts 原测试的构造、公开调用和窗口消息入口。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_XDM_TS_OBSERVATIONS
if (!output) throw new Error('缺少 XDM 原输入采集路径')
const sdk = path.resolve(path.dirname(expect.getState().testPath), '../../../..')
const modulePath = path.join(sdk, 'src/wallet/substrates/XDM.ts')
const occurrenceByTest = new Map()
const sequenceByTest = new Map()
const wrappedWindows = new WeakSet()
let occurrence = 0

function current () { return expect.getState().currentTestName }
function sourceLine () {
  const location = new Error().stack.match(/\/XDM\.test\.ts:(\d+):\d+/)
  if (!location) throw new Error('XDM 入口缺少固定原测试调用站点')
  return Number(location[1])
}
function tag (value, seen = new Map()) {
  if (value === undefined) return { kind: 'Undefined' }
  if (value === null) return { kind: 'Null' }
  if (typeof value === 'string') return { kind: 'String', value }
  if (typeof value === 'boolean') return { kind: 'Boolean', value }
  if (typeof value === 'number') return { kind: 'Number', value: String(value) }
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
  throw new Error('XDM 原输入暂不支持：' + typeof value)
}
function record (method, args, preState) {
  const test = current()
  if (!test) throw new Error('XDM 入口发生在固定测试之外')
  const key = test + '\0' + occurrence
  const sequence = (sequenceByTest.get(key) || 0) + 1
  sequenceByTest.set(key, sequence)
  fs.appendFileSync(output, JSON.stringify({
    test, occurrence, sequence, source: { file: 'src/wallet/substrates/__tests/XDM.test.ts', line: sourceLine() },
    className: 'XDMSubstrate', method, args: args.map(arg => tag(arg)), preState
  }) + '\n')
}
function hostState () {
  const window = globalThis.window
  return { windowType: typeof window, postMessageType: typeof window?.postMessage,
    parentType: typeof window?.parent, priorEvents: sequenceByTest.get(current() + '\0' + occurrence) || 0 }
}
function wrapWindow (window) {
  if (!window || typeof window !== 'object' || !jest.isMockFunction(window.addEventListener)
      || !window.parent || !jest.isMockFunction(window.parent.postMessage) || wrappedWindows.has(window)) return
  wrappedWindows.add(window)
  const addListener = window.addEventListener
  window.addEventListener = function (type, listener, ...rest) {
    if (type !== 'message') return Reflect.apply(addListener, this, [type, listener, ...rest])
    const wrapped = function (event) {
      record('dispatchMessage', [{ source: event.source === window.parent ? 'Parent' : 'Other',
        origin: event.origin, isTrusted: event.isTrusted, data: event.data }], hostState())
      return Reflect.apply(listener, this, [event])
    }
    return Reflect.apply(addListener, this, [type, wrapped, ...rest])
  }
  const post = window.parent.postMessage
  window.parent.postMessage = function (...args) {
    record('postMessage', args, hostState())
    return Reflect.apply(post, this, args)
  }
}

const existing = Object.getOwnPropertyDescriptor(globalThis, 'window')
if (!existing || existing.configurable) {
  let browserWindow = globalThis.window
  Object.defineProperty(globalThis, 'window', { configurable: true, enumerable: true,
    get () { return browserWindow }, set (value) { browserWindow = value; wrapWindow(value) } })
} else throw new Error('XDM 原窗口属性不可观察')

beforeEach(() => {
  const test = current()
  occurrence = (occurrenceByTest.get(test) || 0) + 1
  occurrenceByTest.set(test, occurrence)
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  const Original = moduleObject.default
  const invoke = Original.prototype.invoke
  Original.prototype.invoke = function (...args) {
    record('invoke', args, hostState())
    return Reflect.apply(invoke, this, args)
  }
  const ProxyClass = new Proxy(Original, {
    construct (target, args, newTarget) {
      record('constructor', args, hostState())
      return Reflect.construct(target, args, newTarget)
    }
  })
  return { ...moduleObject, __esModule: true, default: ProxyClass }
})
