// 固定 WalletWire.integration.test.ts：观察真实二进制传输入口与随机熵。
'use strict'
const fs = require('node:fs')
const path = require('node:path')
const frames = process.env.MIGRATION_WALLET_WIRE_TS_FRAMES
const entropy = process.env.MIGRATION_WALLET_WIRE_TS_ENTROPY
const clock = process.env.MIGRATION_WALLET_WIRE_TS_CLOCK
if (!frames || !entropy || !clock) throw new Error('缺少 WalletWire 探针输出路径')
const sdk = path.resolve(path.dirname(expect.getState().testPath), '../../../..')
const modulePath = path.join(sdk, 'src/wallet/substrates/WalletWireTransceiver.ts')
const NativeDate = globalThis.Date
const fixedLinkageTime = NativeDate.parse('2026-09-27T00:00:00.000Z')
const wrapped = new WeakMap()
const counts = new Map()
const occurrences = new Map()
let currentOccurrence = 0
let randomState = 0x6d2b79f5
let randomIndex = 0

class TestDate extends NativeDate {
  constructor (...args) {
    if (args.length === 0 && current()?.includes('revealCounterpartyKeyLinkage')) {
      super(fixedLinkageTime)
      const test = current()
      const location = new Error().stack.match(/\/WalletWire\.integration\.test\.ts:(\d+):\d+/)
      fs.appendFileSync(clock, JSON.stringify({ test, occurrence: currentOccurrence,
        sequence: next(test, 'sample'), line: location ? Number(location[1]) : null,
        iso: new NativeDate(fixedLinkageTime).toISOString() }) + '\n')
    } else super(...args)
  }
  static now () {
    return current()?.includes('revealCounterpartyKeyLinkage') ? fixedLinkageTime : NativeDate.now()
  }
}
Object.defineProperty(globalThis, 'Date', { configurable: true, value: TestDate })

function current() { return expect.getState().currentTestName }
function next(test, kind) {
  const key = test + '\0' + currentOccurrence + '\0' + kind
  const index = (counts.get(key) || 0) + 1
  counts.set(key, index)
  return index
}
function observeFrame(wireId, method, bytes) {
  const test = current()
  if (!test) throw new Error('WalletWire 传输发生在固定测试之外')
  const location = new Error().stack.match(/\/WalletWire\.integration\.test\.ts:(\d+):\d+/)
  const row = { test, occurrence: currentOccurrence, sequence: next(test, 'sample'),
    line: location ? Number(location[1]) : null,
    callIndex: next(test, 'frame'), wireId, method,
    bytesHex: Buffer.from(bytes).toString('hex') }
  fs.appendFileSync(frames, JSON.stringify(row) + '\n')
}
function wrapWire(wire, wireId) {
  if (wrapped.has(wire)) return
  wrapped.set(wire, wireId)
  for (const method of ['transmitToWalletUint8Array', 'transmitToWallet']) {
    if (typeof wire[method] !== 'function') continue
    const original = wire[method]
    wire[method] = function (message) {
      observeFrame(wireId, method, message)
      return Reflect.apply(original, wire, [message])
    }
  }
}

const originalCrypto = globalThis.crypto
const seededCrypto = { subtle: originalCrypto?.subtle }
Object.defineProperty(seededCrypto, 'getRandomValues', { value(array) {
  for (let index = 0; index < array.length; index++) {
    randomState ^= randomState << 13
    randomState ^= randomState >>> 17
    randomState ^= randomState << 5
    array[index] = randomState >>> 24
  }
  const test = current()
  if (test) {
    const location = new Error().stack.match(/\/WalletWire\.integration\.test\.ts:(\d+):\d+/)
    fs.appendFileSync(entropy, JSON.stringify({ test, occurrence: currentOccurrence,
      sequence: next(test, 'sample'), index: ++randomIndex,
      line: location ? Number(location[1]) : null,
      length: array.length, bytesHex: Buffer.from(array).toString('hex') }) + '\n')
  }
  return array
} })
Object.defineProperty(globalThis, 'crypto', { configurable: true, value: seededCrypto })
beforeEach(() => {
  const test = current()
  currentOccurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, currentOccurrence)
  randomState = 0x6d2b79f5
  randomIndex = 0
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  const Original = moduleObject.default
  const ProxyClass = new Proxy(Original, {
    construct(target, args, newTarget) {
      const instance = Reflect.construct(target, args, newTarget)
      const test = current()
      if (test) wrapWire(args[0], next(test, 'wire'))
      return instance
    }
  })
  return { ...moduleObject, __esModule: true, default: ProxyClass }
})
