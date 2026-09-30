// 固定费率模型原测试：采集构造实参和 computeFee 接收的真实交易对象。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_FEE_MODEL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 MIGRATION_FEE_MODEL_TS_OBSERVATIONS')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modelPath = path.join(sdk, 'src/transaction/fee-models/SatoshisPerKilobyte.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0

beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function callLine () {
  const line = new Error().stack.match(/SatoshisPerKilobyte\.test\.ts:(\d+):\d+/)
  if (!line) throw new Error('费率模型原测试调用缺少源码位置')
  return Number(line[1])
}

function observe (method, args, result, line) {
  const test = expect.getState().currentTestName
  if (!test) return
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    method, args, result, source: { file: sourceFile, line } }) + '\n')
}

function txInput (input) {
  if (typeof input.unlockingScript === 'object') {
    return { kind: 'script', bytesHex: Buffer.from(input.unlockingScript.toBinary()).toString('hex') }
  }
  if (typeof input.unlockingScriptTemplate === 'object') return { kind: 'template' }
  return { kind: 'missing' }
}

async function templateDetails (tx, inputs) {
  for (let index = 0; index < inputs.length; index++) {
    if (inputs[index].kind !== 'template') continue
    const mock = tx.inputs[index].unlockingScriptTemplate.estimateLength.mock
    inputs[index].calls = []
    for (let i = 0; i < mock.calls.length; i++) {
      const call = mock.calls[i]
      if (call.length !== 2 || call[0] !== tx) throw new Error('estimateLength 调用结构不同')
      inputs[index].calls.push({ index: call[1], value: await mock.results[i].value })
    }
  }
}

jest.doMock(modelPath, () => {
  const original = jest.requireActual(modelPath)
  const Model = new Proxy(original.default, {
    construct (target, args, newTarget) {
      observe('constructor', args, null, callLine())
      const instance = Reflect.construct(target, args, newTarget)
      return new Proxy(instance, {
        get (object, property) {
          const value = Reflect.get(object, property, object)
          if (property !== 'computeFee') return value
          return async function (tx) {
            const line = callLine()
            const inputs = tx.inputs.map(txInput)
            const descriptor = { rate: object.value, version: tx.version, lockTime: tx.lockTime, inputs,
              outputs: tx.outputs.map(out => ({ satoshis: out.satoshis,
                bytesHex: Buffer.from(out.lockingScript.toBinary()).toString('hex') })) }
            try {
              const fee = await Reflect.apply(value, object, [tx])
              await templateDetails(tx, inputs)
              observe('computeFee', [descriptor], { kind: 'return', fee }, line)
              return fee
            } catch (error) {
              await templateDetails(tx, inputs)
              observe('computeFee', [descriptor], { kind: 'throw', name: error.constructor.name,
                message: error.message }, line)
              throw error
            }
          }
        }
      })
    }
  })
  return { ...original, default: Model, __esModule: true }
})
