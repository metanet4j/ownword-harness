// 通用 Jest 断言轨迹采集：不改变原测试，只记录每个 matcher 的实际 received/异常。
const fs = require('node:fs')
const nativeExpect = global.expect
const output = process.env.MIGRATION_PARITY_TS_OBSERVATIONS
if (!output) throw new Error('缺少 MIGRATION_PARITY_TS_OBSERVATIONS')
const counters = new Map()

function canonical(value, depth = 0) {
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
  if (Array.isArray(value)) return { type: 'array', value: value.map(v => canonical(v, depth + 1)) }
  if (value instanceof Uint8Array || Buffer.isBuffer(value)) {
    return { type: 'array', value: Array.from(value, b => ({ type: 'number', value: String(b & 0xff) })) }
  }
  if (value instanceof Error) return thrown(value)
  if (value instanceof Map) {
    return { type: 'array', value: Array.from(value.entries(), ([k, v]) => canonical(v, depth + 1)) }
  }
  if (value instanceof Set) return { type: 'array', value: Array.from(value, v => canonical(v, depth + 1)) }
  if (typeof value === 'bigint') return { type: 'number', value: value.toString() }
  if (value && typeof value === 'object' && Array.isArray(value.words)) return { type: 'bigNumber', value: String(value) }
  return { type: 'string', value: String(value) }
}

function thrown(error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  const mapped = name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name
  return { kind: 'throw', name: mapped, message: error && error.message !== undefined ? String(error.message) : undefined }
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
  if (matcher === 'toHaveBeenCalledTimes') {
    const count = received && received.mock ? received.mock.calls.length : 0
    return { receiver: received, getActual: () => canonical(count) }
  }
  return { receiver: received, getActual: () => canonical(received) }
}

function wrapAssertion(assertion, received, negated) {
  return new Proxy(assertion, {
    get(target, prop) {
      if (prop === 'not') return wrapAssertion(target.not, received, true)
      const original = target[prop]
      if (typeof original !== 'function') return original
      const matcher = String(prop)
      return (...args) => {
        const { receiver, getActual } = matcherReceiver(received, matcher)
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
          const test = nativeExpect.getState().currentTestName || '<unknown>'
          const key = test + ':' + (negated ? 'not.' : '') + matcher
          const index = (counters.get(key) || 0) + 1
          counters.set(key, index)
          const row = {
            test,
            index,
            matcher: (negated ? 'not.' : '') + matcher,
            negated,
            actual: failure ? thrown(failure) : getActual(),
            expected: args.length === 1 ? canonical(args[0]) : args.map(a => canonical(a)),
            pass: failure === null
          }
          fs.appendFileSync(output, JSON.stringify(row) + '\n')
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
