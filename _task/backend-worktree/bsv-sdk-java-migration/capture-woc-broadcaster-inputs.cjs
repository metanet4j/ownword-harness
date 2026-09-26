// 固定 WhatsOnChainBroadcaster 原测试：记录实际 HTTP 请求、响应和广播结果。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_WOC_BROADCASTER_TS_OBSERVATIONS
if (!output) throw new Error('缺少 WhatsOnChainBroadcaster 输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/broadcasters/WhatsOnChainBroadcaster.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function copy (value) { return JSON.parse(JSON.stringify(value)) }

jest.doMock(modulePath, () => {
  const Original = jest.requireActual(modulePath).default
  return { __esModule: true, default: class ObservedWhatsOnChainBroadcaster extends Original {
    async broadcast (tx) {
      const line = new Error().stack.match(/WhatsOnChainBroadcaster\.test\.ts:(\d+):\d+/)
      if (!line) throw new Error('广播原测试缺少源码调用位置')
      const client = this.httpClient
      const request = client.request.bind(client)
      let observed
      client.request = async (url, options) => {
        if (observed) throw new Error('广播原测试出现额外 HTTP 请求')
        observed = { url, options: copy(options) }
        try {
          const response = await request(url, options)
          observed.response = copy(response)
          return response
        } catch (error) {
          observed.error = { name: error.name, message: error.message }
          throw error
        }
      }
      try {
        const result = await super.broadcast(tx)
        if (!observed) throw new Error('广播原测试未触达 HTTP 请求')
        const value = {
          test: expect.getState().currentTestName, occurrence, sequence: ++sequence,
          source: { file: sourceFile, line: Number(line[1]) }, method: 'broadcast',
          args: [{ network: this.network, client: client.constructor.name, request: observed }],
          result: copy(result)
        }
        fs.appendFileSync(output, JSON.stringify(value) + '\n')
        return result
      } finally {
        client.request = request
      }
    }
  } }
})
