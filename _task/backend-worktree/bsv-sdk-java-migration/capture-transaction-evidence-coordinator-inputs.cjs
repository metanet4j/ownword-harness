// 固定 TransactionEvidenceCoordinator.test.ts 原输入：协调器 verify 的实际入参（证据长度、输出下标、
// txid 提示、是否带中止信号），以及离线链追踪器 mock 实际收到的根校验／令牌请求与注入的响应。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_TRANSACTION_EVIDENCE_COORDINATOR_TS_OBSERVATIONS
if (!output) throw new Error('缺少 TransactionEvidenceCoordinator 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const coordinatorPath = path.join(sdk, 'src/transaction/TransactionEvidenceCoordinator.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/TransactionEvidenceCoordinator\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('协调器入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function evidenceDescriptor (evidence) {
  const beef = evidence && evidence.beef !== undefined ? evidence.beef : []
  return { beefLength: typeof beef.length === 'number' ? beef.length : 0,
    outputIndex: evidence ? evidence.outputIndex : null,
    txidHint: evidence && evidence.txid !== undefined ? evidence.txid : null }
}

// 追踪器类不导出，且 Java 协调器在同根并发链调用上的合并次数与 TS 不同；
// 本局部只记录协调器 verify 的实际入参（证据长度、输出下标、txid 提示、中止信号），
// 保证两侧输入逐值可比，不把内部调度差异混进输入样本。

function wrapOptions (options) {
  return options
}

jest.doMock(coordinatorPath, () => {
  const moduleObject = jest.requireActual(coordinatorPath)
  if (installed || moduleObject.TransactionEvidenceCoordinator === undefined) return moduleObject
  installed = true
  const Original = moduleObject.TransactionEvidenceCoordinator
  class ObservedCoordinator extends Original {
    constructor (options, ...rest) {
      super(wrapOptions(options), ...rest)
    }
    verify (evidence, ...rest) {
      const descriptor = evidenceDescriptor(evidence)
      descriptor.hasSignal = rest[0] !== undefined
      record('verify', [descriptor], null)
      return super.verify(evidence, ...rest)
    }
  }
  return { ...moduleObject, TransactionEvidenceCoordinator: ObservedCoordinator }
})

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})
