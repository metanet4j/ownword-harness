// 固定 TransactionEvidence.test.ts 原输入：parseEvidence 的 evidence 实参（含畸形值）、
// 返回的候选 txid／输出数，以及 assertEvidenceUnchanged 的实际异常。固定私钥、无随机来源。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_TRANSACTION_EVIDENCE_TS_OBSERVATIONS
if (!output) throw new Error('缺少 TransactionEvidence 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/TransactionEvidence.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/TransactionEvidence\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('TransactionEvidence 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function beefDescriptor (value) {
  if (typeof value === 'string') return { kind: 'string', value }
  if (Array.isArray(value) || value instanceof Uint8Array) return { kind: 'array', value: Array.from(value) }
  return { kind: 'other', value: String(value) }
}
function evidenceDescriptor (evidence) {
  return { beef: beefDescriptor(evidence.beef), outputIndex: evidence.outputIndex, txid: evidence.txid ?? null }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed) return moduleObject
  installed = true
  const parseOriginal = moduleObject.parseEvidence
  const assertOriginal = moduleObject.assertEvidenceUnchanged
  moduleObject.parseEvidence = function (...args) {
    const descriptor = evidenceDescriptor(args[0])
    try {
      const candidate = Reflect.apply(parseOriginal, this, args)
      record('parseEvidence', [descriptor], { txid: candidate.txid, outputCount: candidate.tx.outputs.length })
      return candidate
    } catch (error) {
      record('parseEvidence', [descriptor], thrown(error))
      throw error
    }
  }
  moduleObject.assertEvidenceUnchanged = function (...args) {
    try {
      const result = Reflect.apply(assertOriginal, this, args)
      record('assertEvidenceUnchanged', [], { kind: 'return' })
      return result
    } catch (error) {
      record('assertEvidenceUnchanged', [], thrown(error))
      throw error
    }
  }
  return moduleObject
})
