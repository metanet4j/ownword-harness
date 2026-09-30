// 固定 Teranode 原测试：记录构造实参、实际二进制请求及响应。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_TERANODE_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Teranode 输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/broadcasters/Teranode.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function source () {
  const line = new Error().stack.match(/Teranode\.test\.ts:(\d+):\d+/)
  if (!line) throw new Error('Teranode 原测试缺少源码调用位置')
  return { file: sourceFile, line: Number(line[1]) }
}

function clientKind (client) {
  const name = client?.constructor?.name
  if (name === 'BinaryFetchClient') return 'binary-fetch'
  if (name === 'NodejsHttpClient') return 'nodejs-https'
  if (typeof client?.request === 'function') return 'mock-http'
  throw new Error('Teranode 原客户端缺少 request')
}

function value (item) {
  if (item === undefined) return { kind: 'Undefined' }
  if (item === null) return { kind: 'Null' }
  if (typeof item === 'string') return { kind: 'String', value: item }
  if (typeof item === 'number') return { kind: 'Number', value: String(item) }
  if (typeof item === 'boolean') return { kind: 'Boolean', value: item }
  if (Array.isArray(item)) return { kind: 'Array', value: item.map(value) }
  if (typeof item === 'object') {
    if (item instanceof Error) return { kind: 'Error', name: item.name, message: value(item.message) }
    return { kind: 'Object', fields: Object.fromEntries(Object.entries(item).map(([k, v]) => [k, value(v)])) }
  }
  throw new Error(`Teranode 原值未表征：${typeof item}`)
}

function write (method, args, result, site) {
  fs.appendFileSync(output, JSON.stringify({ test: expect.getState().currentTestName,
    occurrence, sequence: ++sequence, method, args, result, source: site }) + '\n')
}

jest.doMock(modulePath, () => {
  const Original = jest.requireActual(modulePath).default
  return { __esModule: true, default: class ObservedTeranode extends Original {
    constructor (...args) {
      const site = source()
      super(...args)
      write('constructor', [{ url: args[0], client: args.length > 1 ? clientKind(args[1]) : 'default' }],
        { url: this.URL, client: clientKind(this.httpClient) }, site)
    }

    async broadcast (tx) {
      const site = source()
      const client = this.httpClient
      const request = client.request.bind(client)
      let observed
      client.request = async (url, options) => {
        if (observed) throw new Error('Teranode 原测试出现额外 HTTP 请求')
        if (!(options.data instanceof Blob)) throw new Error('Teranode 原请求体不是 Blob')
        observed = { url, options: { method: options.method, headers: { ...options.headers },
          data: { kind: 'Blob', bytesHex: Buffer.from(await options.data.arrayBuffer()).toString('hex'),
            type: options.data.type } } }
        try {
          const response = await request(url, options)
          observed.response = { ok: response.ok, status: response.status,
            statusText: response.statusText, data: value(response.data) }
          return response
        } catch (error) {
          observed.error = value(error)
          throw error
        }
      }
      try {
        const result = await super.broadcast(tx)
        if (!observed) throw new Error('Teranode 原测试未触达 HTTP 请求')
        write('broadcast', [{ url: this.URL, client: clientKind(client), request: observed }], result, site)
        return result
      } finally {
        client.request = request
      }
    }
  } }
})
