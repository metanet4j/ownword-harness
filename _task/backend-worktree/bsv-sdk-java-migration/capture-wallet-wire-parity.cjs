// WalletWire 原断言轨迹；大字节数组按长度及 SHA-256 记录，避免 4 MiB BEEF 展开。
const fs = require('node:fs')
const path = require('node:path')
const crypto = require('node:crypto')
const nativeExpect = global.expect
const output = process.env.MIGRATION_PARITY_TS_OBSERVATIONS
if (!output) throw new Error('缺少 MIGRATION_PARITY_TS_OBSERVATIONS')
const largeOutput = process.env.MIGRATION_WALLET_WIRE_TS_LARGE_ACTUALS
const assertionIndexPath = process.env.MIGRATION_WALLET_WIRE_ASSERTION_INDEX
if (largeOutput && !assertionIndexPath) throw new Error('大型 WalletWire actual 缺少独立断言索引')
const assertionIndex = assertionIndexPath
  ? new Map(JSON.parse(fs.readFileSync(assertionIndexPath, 'utf8')).map(row => [
    `${row.test}\0${row.occurrence}\0${row.ordinal}`, row
  ])) : null
const counters = new Map()
const ordinals = new Map()
const occurrences = new Map()
let currentOccurrence = 0
beforeEach(() => {
  const state = nativeExpect.getState()
  const key = `${state.testPath || ''}\0${state.currentTestName || ''}`
  currentOccurrence = (occurrences.get(key) || 0) + 1
  occurrences.set(key, currentOccurrence)
})

function largeBytes(bytes) {
  return { type: 'map', value: {
    length: { type: 'number', value: String(bytes.length) },
    sha256: { type: 'string', value: crypto.createHash('sha256').update(Buffer.from(bytes)).digest('hex') }
  } }
}

function rawLargeBytes(value) {
  if (value instanceof Uint8Array || Buffer.isBuffer(value))
    return value.length > 65536 ? Buffer.from(value) : null
  if (Array.isArray(value) && value.length > 65536 &&
      value.every(item => Number.isInteger(item) && item >= 0 && item <= 255))
    return Buffer.from(value)
  return null
}

function canonical(value, depth = 0, deepObjects = false) {
  if (depth > 8) return { type: 'string', value: '[depth-limit]' }
  if (value === undefined) return { type: 'undefined' }
  if (value === null) return { type: 'null' }
  if (typeof value === 'boolean') return { type: 'boolean', value }
  if (typeof value === 'number') {
    if (Number.isNaN(value)) return { type: 'number', value: 'NaN' }
    if (!Number.isFinite(value)) return { type: 'number', value: value > 0 ? 'Infinity' : '-Infinity' }
    return { type: 'number', value: Object.is(value, -0) ? '0' : String(value) }
  }
  if (typeof value === 'string') return { type: 'string', value }
  if (Array.isArray(value)) {
    if (value.length > 65536 && value.every(v => Number.isInteger(v) && v >= 0 && v <= 255))
      return largeBytes(value)
    return { type: 'array', value: value.map(v => canonical(v, depth + 1, deepObjects)) }
  }
  if (value instanceof Uint8Array || Buffer.isBuffer(value)) {
    if (value.length > 65536) return largeBytes(value)
    return { type: 'array', value: Array.from(value, b => ({ type: 'number', value: String(b & 0xff) })) }
  }
  if (value instanceof Error) return thrown(value)
  if (value instanceof Map) {
    return { type: 'array', value: Array.from(value.entries(), ([k, v]) => canonical(v, depth + 1, deepObjects)) }
  }
  if (value instanceof Set) return { type: 'array', value: Array.from(value, v => canonical(v, depth + 1, deepObjects)) }
  if (typeof value === 'bigint') return { type: 'number', value: value.toString() }
  if (value && typeof value === 'object' && Array.isArray(value.words)) return { type: 'bigNumber', value: String(value) }
  if (deepObjects && value && typeof value === 'object' && (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null)) {
    return { type: 'map', value: Object.fromEntries(Object.entries(value).map(([key, item]) => [key, canonical(item, depth + 1, true)])) }
  }
  return { type: 'string', value: String(value) }
}

function thrown(error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  const mapped = name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name
  return { kind: 'throw', name: mapped, message: error && error.message !== undefined ? String(error.message) : undefined }
}

function canonicalCallArg(value) {
  if (typeof value === 'function') return { type: 'string', value: value.name || '<anonymous>' }
  return canonical(value)
}

function canonicalCalls(calls) {
  return { type: 'array', value: calls.map(args => ({
    type: 'array', value: args.map(canonicalCallArg)
  })) }
}

function matcherReceiver(received, matcher) {
  if ((matcher === 'toThrow') && typeof received === 'function') {
    let outcome = null
    const wrapped = function (...args) {
      try {
        const result = received.apply(this, args)
        outcome = { kind: 'return', value: canonical(result) }
        return result
      } catch (error) {
        outcome = { kind: 'throw', name: thrown(error).name, message: error.message }
        throw error
      }
    }
    return { receiver: wrapped, getActual: () => outcome || { kind: 'throw', name: 'Error', message: 'not executed' } }
  }
  if (matcher === 'toHaveLength') return { receiver: received, getActual: () => canonical(received.length) }
  if (matcher === 'toHaveBeenCalledTimes' || matcher === 'toHaveBeenCalled') {
    const count = received && received.mock ? received.mock.calls.length : 0
    return { receiver: received, getActual: () => canonical(count) }
  }
  if (matcher === 'toHaveBeenCalledWith') {
    return { receiver: received, getActual: () => canonicalCalls(received.mock.calls) }
  }
  return { receiver: received, getActual: () => canonical(received, 0, matcher === 'toEqual') }
}

function wrapAssertion(assertion, received, negated, promiseMode = null) {
  return new Proxy(assertion, {
    get(target, prop) {
      if (prop === 'not') return wrapAssertion(target.not, received, true, promiseMode)
      if (prop === 'rejects' || prop === 'resolves') return wrapAssertion(target[prop], received, negated, prop)
      const original = target[prop]
      if (typeof original !== 'function') return original
      const matcher = String(prop)
      return (...args) => {
        const { receiver, getActual } = matcherReceiver(received, matcher)
        const append = (actual, pass) => {
          const test = nativeExpect.getState().currentTestName || '<unknown>'
          const key = test + ':' + (negated ? 'not.' : '') + matcher
          const index = (counters.get(key) || 0) + 1
          counters.set(key, index)
          const ordinalKey = `${test}\0${currentOccurrence}`
          const ordinal = (ordinals.get(ordinalKey) || 0) + 1
          ordinals.set(ordinalKey, ordinal)
          const row = {
            test,
            file: path.normalize(nativeExpect.getState().testPath || ''),
            occurrence: currentOccurrence,
            index,
            matcher: (negated ? 'not.' : '') + matcher,
            negated,
            actual,
            expected: matcher === 'toHaveBeenCalledWith'
              ? { type: 'array', value: args.map(canonicalCallArg) }
              : args.length === 1
              ? (matcher === 'toBeInstanceOf' ? canonical(args[0].name) : canonical(args[0], 0, matcher === 'toEqual'))
              : args.map(a => canonical(a, 0, matcher === 'toEqual')),
            pass
          }
          fs.appendFileSync(output, JSON.stringify(row) + '\n')
          if (largeOutput) {
            const bytes = rawLargeBytes(received)
            if (bytes) {
              const identity = assertionIndex.get(`${test}\0${currentOccurrence}\0${ordinal}`)
              if (!identity) throw new Error('大型 WalletWire actual 未关联冻结断言')
              fs.appendFileSync(largeOutput, JSON.stringify({
                runId: process.env.EVIDENCE_RUN_ID, side: 'ts',
                caseId: identity.caseId, assertionId: identity.assertionId,
                test, occurrence: currentOccurrence, ordinal, matcher: row.matcher,
                length: bytes.length, sha256: crypto.createHash('sha256').update(bytes).digest('hex'),
                bytesHex: bytes.toString('hex')
              }) + '\n')
            }
          }
        }
        if (promiseMode) {
          const observed = Promise.resolve(received).then(
            value => promiseMode === 'resolves' ? canonical(value) : { kind: 'return', value: canonical(value) },
            error => thrown(error)
          )
          return Promise.resolve(Reflect.apply(original, target, args)).then(
            async value => { append(await observed, true); return value },
            async error => { append(await observed, false); throw error }
          )
        }
        let failure = null
        try {
          if (matcher === 'toThrow') {
            const fresh = nativeExpect(receiver)
            const freshTarget = negated ? fresh.not : fresh
            return Reflect.apply(freshTarget[matcher], freshTarget, args)
          }
          return Reflect.apply(original, target, args)
        } catch (error) {
          failure = error
          throw error
        } finally {
          append(getActual(), failure === null)
        }
      }
    }
  })
}

function wrappedExpect(actual) {
  return wrapAssertion(nativeExpect(actual), actual, false)
}
Object.assign(wrappedExpect, nativeExpect)
global.expect = wrappedExpect
