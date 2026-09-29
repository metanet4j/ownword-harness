// 固定 window.CWI.test.ts 原输入：构造时的窗口绑定状态，以及宿主 CWI mock 收到的每次调用与返回值。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_WINDOW_CWI_TS_OBSERVATIONS
if (!output) throw new Error('缺少 window.CWI 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/wallet/substrates/window.CWI.ts')
const occurrences = new Map()
const sequenceByTest = new Map()
const wrappedCwi = new WeakSet()
let occurrence = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/window\.CWI\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('window.CWI 入口发生在固定测试之外')
  const key = test + '\0' + occurrence
  const sequence = (sequenceByTest.get(key) || 0) + 1
  sequenceByTest.set(key, sequence)
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence,
    source: { file: sourceFile, line }, method, args: args.map(arg => tag(arg)), result }) + '\n')
}
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
  if (value instanceof Uint8Array) return { kind: 'Array', value: Array.from(value, item => tag(item)) }
  if (Array.isArray(value)) return { kind: 'Array', value: value.map(item => tag(item)) }
  if (typeof value === 'object') {
    const entries = {}
    for (const key of Object.keys(value).sort()) entries[key] = tag(value[key])
    return { kind: 'Object', entries }
  }
  throw new Error('window.CWI 原输入暂不支持：' + typeof value)
}
function windowState () {
  return { window: typeof globalThis.window, cwi: typeof globalThis.window?.CWI }
}
// 保留 jest mock 身份（原断言核对实参与返回值），只在实现外记录模块真正交给 CWI 的调用。
function wrapCwi (cwi) {
  if (!cwi || typeof cwi !== 'object' || wrappedCwi.has(cwi)) return
  wrappedCwi.add(cwi)
  for (const key of Object.keys(cwi)) {
    const mock = cwi[key]
    if (!jest.isMockFunction(mock)) continue
    const original = mock.getMockImplementation()
    mock.mockImplementation(async function (...args) {
      const line = callLine()
      try {
        const value = await Reflect.apply(original, this, args)
        record(key, args, tag(value), line)
        return value
      } catch (error) {
        record(key, args, thrown(error), line)
        throw error
      }
    })
  }
}

const existing = Object.getOwnPropertyDescriptor(globalThis, 'window')
if (!existing || existing.configurable) {
  let currentWindow = globalThis.window
  Object.defineProperty(globalThis, 'window', { configurable: true, enumerable: true,
    get () { return currentWindow },
    set (value) { currentWindow = value; wrapCwi(value?.CWI) } })
} else throw new Error('window.CWI 原 window 属性不可观察')

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  const Original = moduleObject.default
  const ProxyClass = new Proxy(Original, {
    construct (target, args, newTarget) {
      const line = callLine()
      const state = windowState()
      try {
        const instance = Reflect.construct(target, args, newTarget)
        record('constructor', [state], null, line)
        return instance
      } catch (error) {
        record('constructor', [state], thrown(error), line)
        throw error
      }
    }
  })
  return { ...moduleObject, __esModule: true, default: ProxyClass }
})
