// 观察固定 Transaction.test.ts 向量实际传入公开 SDK 方法的参数。
const fs = require('node:fs')
const path = require('node:path')

const catalog = JSON.parse(fs.readFileSync(process.env.MIGRATION_VECTOR_CATALOG, 'utf8'))
const mapping = JSON.parse(fs.readFileSync(process.env.MIGRATION_VECTOR_MAPPING, 'utf8'))
const output = process.env.MIGRATION_VECTOR_TS_INPUTS
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少 Transaction 向量采集身份')

const testPath = expect.getState().testPath
const source = catalog.files.find(file => testPath.endsWith('/' + file.path))
if (!source || source.path !== 'src/transaction/__tests/Transaction.test.ts') {
  throw new Error('固定 Transaction 原测试路径变化')
}
const mapped = new Map(mapping.cases.map(row => [row.id, row.java]))
const names = new Map(source.cases.filter(row => mapped.get(row.id)?.some(java =>
  java.className === 'com.metanet4j.bsv.transaction.TransactionCompleteVectorsTest'))
  .map(row => [row.names.join(' ') + '\0' + row.occurrence, row.id]))
const occurrences = new Map()
let active

function append(input) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId: active,
    test: expect.getState().currentTestName, input }) + '\n')
}

function decimal(value) {
  if (!Number.isSafeInteger(value)) throw new Error('Transaction 向量数值超出安全整数')
  return String(value)
}

beforeEach(() => {
  const name = expect.getState().currentTestName
  const occurrence = (occurrences.get(name) || 0) + 1
  occurrences.set(name, occurrence)
  active = names.get(name + '\0' + occurrence)
  if (!active) return

  const Transaction = jest.requireActual(path.resolve(path.dirname(testPath), '../Transaction.ts')).default
  const TransactionSignature = jest.requireActual(path.resolve(path.dirname(testPath), '../../primitives/TransactionSignature.ts')).default
  let inFromHex = false
  const originalFromBinary = Transaction.fromBinary
  const originalFromHex = Transaction.fromHex
  const originalFormat = TransactionSignature.format

  jest.spyOn(Transaction, 'fromBinary').mockImplementation(function (...args) {
    if (!inFromHex) {
      if (args.length !== 1 || !Array.isArray(args[0])) throw new Error('固定 fromBinary 参数变化')
      append({ method: 'Transaction.fromBinary', args: [Buffer.from(args[0]).toString('hex')] })
    }
    return Reflect.apply(originalFromBinary, this, args)
  })
  jest.spyOn(Transaction, 'fromHex').mockImplementation(function (...args) {
    if (args.length !== 1 || typeof args[0] !== 'string') throw new Error('固定 fromHex 参数变化')
    append({ method: 'Transaction.fromHex', args })
    inFromHex = true
    try { return Reflect.apply(originalFromHex, this, args) } finally { inFromHex = false }
  })
  jest.spyOn(TransactionSignature, 'format').mockImplementation(function (...args) {
    if (args.length !== 1) throw new Error('固定 sighash 格式参数变化')
    const p = args[0]
    if (typeof p.sourceTXID !== 'string' || typeof p.subscript?.toHex !== 'function' ||
        typeof p.ignoreChronicle !== 'boolean' || !Array.isArray(p.otherInputs) || !Array.isArray(p.outputs)) {
      throw new Error('固定 sighash 参数类型变化')
    }
    append({ operation: 'sighash-format', args: [{
      sourceTXID: p.sourceTXID,
      sourceOutputIndex: decimal(p.sourceOutputIndex),
      sourceSatoshis: decimal(p.sourceSatoshis),
      transactionVersion: decimal(p.transactionVersion),
      otherInputs: decimal(p.otherInputs.length),
      outputs: decimal(p.outputs.length),
      inputIndex: decimal(p.inputIndex),
      subscriptHex: p.subscript.toHex(),
      inputSequence: decimal(p.inputSequence),
      lockTime: decimal(p.lockTime),
      scope: decimal(p.scope),
      ignoreChronicle: p.ignoreChronicle
    }] })
    return Reflect.apply(originalFormat, this, args)
  })
})

afterEach(() => { active = undefined; jest.restoreAllMocks() })
