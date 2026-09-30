// 固定 ARC 原测试：记录真实随机字节、HTTP 请求、响应和广播结果。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_ARC_TS_OBSERVATIONS
const randomOutput = process.env.MIGRATION_ARC_RANDOM_OBSERVATIONS
if (!output || !randomOutput) throw new Error('缺少 ARC 输入或随机采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/broadcasters/ARC.ts')
const randomPath = path.join(sdk, 'src/primitives/Random.ts')
const frozen = process.env.MIGRATION_ARC_RANDOM_REPLAY
  ? JSON.parse(fs.readFileSync(process.env.MIGRATION_ARC_RANDOM_REPLAY, 'utf8')) : null
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let randomIndex = 0

afterAll(() => {
  if (frozen && randomIndex !== frozen.length) throw new Error('ARC 冻结随机输入未全部消费')
})

beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function copy (value) { return JSON.parse(JSON.stringify(value)) }

jest.doMock(randomPath, () => {
  const original = jest.requireActual(randomPath)
  return { ...original, default: function (length) {
    const test = expect.getState().currentTestName
    const entry = frozen?.[randomIndex++]
    if (frozen && (!entry || entry.test !== test || entry.occurrence !== occurrence || entry.length !== length))
      throw new Error('ARC 冻结随机输入的原用例或长度不匹配')
    const bytes = entry ? Array.from(Buffer.from(entry.hex, 'hex')) : original.default(length)
    if (bytes.length !== length) throw new Error('ARC 冻结随机字节数不匹配')
    fs.appendFileSync(randomOutput, JSON.stringify({ test, occurrence, length,
      hex: Buffer.from(bytes).toString('hex') }) + '\n')
    return bytes
  }, __esModule: true }
})

jest.doMock(modulePath, () => {
  const Original = jest.requireActual(modulePath).default
  return { __esModule: true, default: class ObservedARC extends Original {
    async broadcast (tx) {
      const line = new Error().stack.match(/ARC\.test\.ts:(\d+):\d+/)
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
          args: [{ url: this.URL, client: client.constructor.name, request: observed }],
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
