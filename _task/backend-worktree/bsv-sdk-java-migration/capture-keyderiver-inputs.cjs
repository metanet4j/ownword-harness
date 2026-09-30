// 固定 KeyDeriver.test.ts：只记录原测试直接发起的构造与公开方法调用。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_KEYDERIVER_TS_INPUTS
if (!output) throw new Error('缺少 KeyDeriver 原输入采集路径')
const sdk = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk')
const modulePath = path.join(sdk, 'src/wallet/KeyDeriver.ts')
const file = 'src/wallet/__tests/KeyDeriver.test.ts'
const METHODS = ['computeInvoiceNumber', 'normalizeCounterparty', 'derivePublicKey', 'derivePrivateKey',
  'derivePrivateKeys', 'deriveSymmetricKey', 'revealCounterpartySecret', 'revealSpecificSecret']
const occurrenceByTest = new Map()
const sequenceByTest = new Map()
let occurrence = 0

function current () { return expect.getState().currentTestName }
function lineOf () {
  const location = new Error().stack.match(/\/KeyDeriver\.test\.ts:(\d+):\d+/)
  if (!location) throw new Error('KeyDeriver 入口缺少固定原测试调用站点')
  return Number(location[1])
}
/** 立即调用者不是原测试时属于实现内部自调用，不进入边界账本。 */
function fromTest () {
  const frames = new Error().stack.split('\n').slice(1)
  const caller = frames.find(frame => /KeyDeriver\.(test\.ts|ts)/.test(frame))
  return Boolean(caller && /KeyDeriver\.test\.ts/.test(caller))
}
function keyIdentity (value) {
  const name = value?.constructor?.name
  if (!['PublicKey', 'PrivateKey', 'SymmetricKey'].includes(name)) return null
  const hex = typeof value.toHex === 'function' ? value.toHex() : value.toString()
  return { kind: name, hex }
}
function tag (value, seen = new Map()) {
  if (value === undefined) return { kind: 'Undefined' }
  if (value === null) return { kind: 'Null' }
  if (typeof value === 'string') return { kind: 'String', value }
  if (typeof value === 'boolean') return { kind: 'Boolean', value }
  if (typeof value === 'number') return { kind: 'Number', value: String(value) }
  if (typeof value === 'function') {
    if (!jest.isMockFunction(value)) throw new Error('KeyDeriver 收到未支持的函数输入')
    return { kind: 'JestMock', source: String(value) }
  }
  const key = keyIdentity(value)
  if (key) return key
  if (Array.isArray(value)) {
    if (seen.has(value)) return { kind: 'Ref', id: seen.get(value) }
    const id = seen.size + 1; seen.set(value, id)
    return { kind: 'Array', id, value: value.map(item => tag(item, seen)) }
  }
  if (typeof value === 'object') {
    if (seen.has(value)) return { kind: 'Ref', id: seen.get(value) }
    const id = seen.size + 1; seen.set(value, id)
    const entries = {}
    for (const name of Object.keys(value).sort()) entries[name] = tag(value[name], seen)
    return { kind: 'Object', id, entries }
  }
  throw new Error('KeyDeriver 原输入暂不支持：' + typeof value)
}
function record (method, args, line) {
  const test = current()
  if (!test) throw new Error('KeyDeriver 入口发生在固定测试之外')
  const key = test + '\0' + occurrence
  const sequence = (sequenceByTest.get(key) || 0) + 1
  sequenceByTest.set(key, sequence)
  const row = { test, occurrence, sequence, source: { file, line }, className: 'KeyDeriver', method,
    args: args.map(arg => tag(arg)),
    preState: { priorEvents: sequence - 1 } }
  fs.appendFileSync(output, JSON.stringify(row) + '\n')
  return row
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrenceByTest.get(test) || 0) + 1
  occurrenceByTest.set(test, occurrence)
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  const Original = moduleObject.default
  const ProxyClass = new Proxy(Original, {
    construct (target, args, newTarget) {
      record('constructor', args, lineOf())
      const instance = Reflect.construct(target, args, newTarget)
      for (const name of METHODS) {
        const original = instance[name]
        if (typeof original !== 'function') throw new Error('KeyDeriver 缺少原方法：' + name)
        instance[name] = function (...methodArgs) {
          if (fromTest()) record(name, methodArgs, lineOf())
          return Reflect.apply(original, this, methodArgs)
        }
      }
      return instance
    }
  })
  return { ...moduleObject, __esModule: true, default: ProxyClass }
})
