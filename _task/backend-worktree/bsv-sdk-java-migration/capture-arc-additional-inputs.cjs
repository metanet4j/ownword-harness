// ARC.additional 原入口、随机输入及外部替身回调；不改变固定原测试。
'use strict'
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.MIGRATION_ARC_ADDITIONAL_INPUTS
const randomOutput = process.env.MIGRATION_ARC_ADDITIONAL_RANDOM_OUTPUT
if (!output || !randomOutput) throw new Error('缺少 ARC.additional 采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const arcPath = path.join(sdk, 'src/transaction/broadcasters/ARC.ts')
const randomPath = path.join(sdk, 'src/primitives/Random.ts')
const frozen = process.env.MIGRATION_ARC_ADDITIONAL_RANDOM
  ? JSON.parse(fs.readFileSync(process.env.MIGRATION_ARC_ADDITIONAL_RANDOM, 'utf8')) : null
let sequence = 0
let randomIndex = 0
let activeSource
beforeEach(() => { sequence = 0; activeSource = null })
afterAll(() => { if (frozen && randomIndex !== frozen.length) throw new Error('随机输入未全部消费') })
function encode (value) {
  if (value === undefined) return { type: 'undefined' }
  if (value === null) return { type: 'null' }
  if (['string', 'number', 'boolean'].includes(typeof value)) return { type: typeof value, value }
  if (typeof value === 'function') return { type: 'function', name: value.name }
  if (value instanceof Error) return { type: 'Error', name: value.name, message: encode(value.message) }
  if (Array.isArray(value)) return { type: 'array', value: value.map(encode) }
  if (typeof value.request === 'function') return { type: 'HttpClient', name: value.constructor.name }
  if (typeof value.toHex === 'function' && typeof value.toHexEF === 'function')
    return { type: 'TransactionFixture', methods: ['toHex', 'toHexEF'] }
  return { type: 'object', value: Object.fromEntries(Object.keys(value).sort().map(key => [key, encode(value[key])])) }
}
function source () {
  const match = new Error().stack.match(/ARC\.additional\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('缺少原 ARC.additional 调用位置')
  return { file: sourceFile, line: Number(match[1]) }
}
function record (method, args, extra = {}) {
  fs.appendFileSync(output, JSON.stringify({ test: expect.getState().currentTestName, occurrence: 1,
    sequence: ++sequence, source: activeSource, method, args: args.map(encode), ...extra }) + '\n')
}
jest.doMock(randomPath, () => {
  const original = jest.requireActual(randomPath)
  return { ...original, __esModule: true, default: function (length) {
    const test = expect.getState().currentTestName
    const entry = frozen?.[randomIndex++]
    if (frozen && (!entry || entry.test !== test || entry.length !== length)) throw new Error('原随机用例/长度不同')
    const bytes = entry ? Array.from(Buffer.from(entry.hex, 'hex')) : original.default(length)
    if (bytes.length !== length) throw new Error('原随机字节数量不同')
    const hex = Buffer.from(bytes).toString('hex')
    fs.appendFileSync(randomOutput, JSON.stringify({ test, length, hex }) + '\n')
    record('Random', [length], { bytesHex: hex })
    return bytes
  } }
})
function wrapTransaction (tx, restorers) {
  for (const method of ['toHex', 'toHexEF']) {
    const own = Object.getOwnPropertyDescriptor(tx, method)
    const original = tx[method]
    tx[method] = function (...args) {
      try {
        const result = Reflect.apply(original, this, args)
        record('Transaction.' + method, args, { returned: encode(result) })
        return result
      } catch (error) {
        record('Transaction.' + method, args, { thrown: encode(error) })
        throw error
      }
    }
    restorers.push(() => own ? Object.defineProperty(tx, method, own) : delete tx[method])
  }
}
jest.doMock(arcPath, () => {
  const original = jest.requireActual(arcPath)
  const Observed = new Proxy(original.default, {
    construct (target, args, newTarget) {
      activeSource = source()
      record('ARC.constructor', args)
      const instance = Reflect.construct(target, args, newTarget)
      return new Proxy(instance, {
        get (target, key, receiver) {
          const value = Reflect.get(target, key, receiver)
          if (!['broadcast', 'broadcastMany'].includes(key)) return value
          return async function (...args) {
            activeSource = source()
            record('ARC.' + key, args)
            const restorers = []
            const transactions = key === 'broadcast' ? args : args[0]
            for (const tx of transactions) wrapTransaction(tx, restorers)
            const client = target.httpClient
            const request = client.request
            client.request = async function (url, options) {
              record('HttpClient.request', [url, options])
              try {
                const response = await Reflect.apply(request, client, [url, options])
                record('HttpClient.response', [response])
                return response
              } catch (error) {
                record('HttpClient.reject', [error])
                throw error
              }
            }
            try {
              const result = await Reflect.apply(value, target, args)
              if (key !== 'broadcastMany' || !Array.isArray(result)) return result
              return new Proxy(result, {
                get (array, property, arrayReceiver) {
                  if (property !== Symbol.iterator) return Reflect.get(array, property, arrayReceiver)
                  return function * () {
                    const loopSource = source()
                    for (const item of array) {
                      activeSource = loopSource
                      record('loop.value', [item])
                      yield item
                    }
                  }
                }
              })
            } finally {
              client.request = request
              restorers.reverse().forEach(restore => restore())
            }
          }
        }
      })
    }
  })
  return { ...original, default: Observed, __esModule: true }
})
