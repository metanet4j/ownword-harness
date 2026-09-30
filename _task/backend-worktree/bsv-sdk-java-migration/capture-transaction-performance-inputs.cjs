// 固定 Transaction.performance.test.ts 原输入：Transaction／Beef／BeefTx 公开入口的实参与确定性结果。
// 该文件虽名为性能用例，但原断言全部是确定性结果（字节相等、规模计数、txid/哈希、异常消息），
// 没有耗时阈值；因此这里逐值登记确定性结果，规模（3000 深链）按真实调用逐次登记，不做抽样。
// Transaction 与 Beef／BeefTx 互相引用，因此只包装真实模块的原型与静态方法，且只安装一次。
'use strict'
const crypto = require('node:crypto')
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_TRANSACTION_PERFORMANCE_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Transaction performance 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const transactionModulePath = path.join(sdk, 'src/transaction/Transaction.ts')
const beefModulePath = path.join(sdk, 'src/transaction/Beef.ts')
const beefTxModulePath = path.join(sdk, 'src/transaction/BeefTx.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
// 非 0 表示正在执行 Java 侧同样不可观测的内部调用（入参描述、静态解析、原方法内部调用）。
let depth = 0
let transactionInstalled = false
let beefInstalled = false
let beefTxInstalled = false

const voidResult = () => null
// 大字节/长文本只比长度与 SHA-256；两侧同一规则，仍是确定性结果的严格相等比较。
const INLINE_LIMIT = 512

function current () { return expect.getState().currentTestName }
// 只有原测试自己写的调用才算入口：SDK 内部（未包装的 getter／方法）再调用已包装方法时，
// 紧邻的调用帧落在 SDK 源码而不是原测试文件；这类调用 Java 侧同样不可观测，不能登记成原输入。
function calledFromTest () {
  for (const frame of new Error().stack.split('\n').slice(1)) {
    if (frame.includes('capture-transaction-performance-inputs.cjs')) continue
    return frame.includes('Transaction.performance.test.ts')
  }
  return false
}
function callLine () {
  const match = new Error().stack.match(/Transaction\.performance\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('Transaction performance 入口缺少固定原测试调用位置')
  return Number(match[1])
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('Transaction performance 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function observe (method, args, action, describe) {
  if (depth !== 0 || !calledFromTest()) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? result : describe(result))
    return result
  } finally {
    depth--
  }
}
// 原方法抛错也登记真实异常，Java 侧按同样的消息重放。
function observeThrow (method, args, action, describe) {
  if (depth !== 0 || !calledFromTest()) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? voidResult() : describe(result))
    return result
  } catch (error) {
    record(method, args, describeThrown(error))
    throw error
  } finally {
    depth--
  }
}
// 异步入口保持 depth 直到落定，避免内部调用被当成原测试入口。
// 调用位置必须在入口同步取栈，落定回调里已经没有原测试帧。
function observeAsync (method, args, action, describe) {
  if (depth !== 0 || !calledFromTest()) return action()
  const line = callLine()
  depth++
  return Promise.resolve(action()).then(result => {
    try {
      record(method, args, describe(result), line)
    } finally {
      depth--
    }
    return result
  }, error => {
    try {
      record(method, args, describeThrown(error), line)
    } finally {
      depth--
    }
    throw error
  })
}
// 描述参数/返回值时调用的公开方法算内部调用，不另记入口。
function describe (build) {
  depth++
  try {
    return build()
  } finally {
    depth--
  }
}
function describeThrown (error) {
  return { kind: 'throw', name: error && error.constructor ? error.constructor.name : String(error),
    message: error && error.message !== undefined ? String(error.message) : String(error) }
}
function jsNumber (value) {
  if (Number.isInteger(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER) return value
  return String(value)
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function blob (kind, hexText) {
  if (hexText.length <= INLINE_LIMIT) return { kind, hex: hexText }
  return { kind, length: hexText.length,
    sha256: crypto.createHash('sha256').update(hexText).digest('hex') }
}
function bytesBlob (kind, bytes) { return blob(kind, hex(bytes)) }
function asm (script) {
  if (script === null || script === undefined) return null
  return describe(() => script.toASM())
}
function inputDescriptor (input) {
  return { sourceTXID: input.sourceTXID ?? null,
    sourceOutputIndex: jsNumber(input.sourceOutputIndex ?? 0),
    unlockingScript: asm(input.unlockingScript ?? null),
    // 原 addInput 在入口处补默认 sequence；两侧都按补默认后的值登记。
    sequence: jsNumber(input.sequence ?? 0xffffffff),
    hasTemplate: typeof input.unlockingScriptTemplate === 'object' && input.unlockingScriptTemplate !== null,
    hasSourceTransaction: typeof input.sourceTransaction === 'object' && input.sourceTransaction !== null }
}
function outputDescriptor (item) {
  return { satoshis: item.satoshis === undefined ? null : jsNumber(item.satoshis),
    lockingScript: asm(item.lockingScript) }
}
function txDescriptor (value) {
  if (value === undefined || value === null) return null
  if (typeof value.id !== 'function') return null
  return describe(() => ({ txid: value.id('hex'), inputs: value.inputs.length, outputs: value.outputs.length }))
}
function beefTxDescriptor (value) {
  if (value === undefined || value === null) return null
  if (typeof value.txid !== 'string') return null
  return { txid: value.txid }
}
function leafDescriptor (leaf) {
  // 调用方传入的路径按输入侧口径登记（不含 txid 标志），与 Java 重放一致。
  return { offset: jsNumber(leaf.offset), hash: leaf.hash }
}
function pathDescriptor (merklePath) {
  if (merklePath === undefined || merklePath === null) return null
  return describe(() => ({ blockHeight: jsNumber(merklePath.blockHeight),
    path: merklePath.path.map(level => level.map(leafDescriptor)) }))
}
function beefDescriptor (beef) {
  return describe(() => ({ txCount: beef.txs.length, bumpCount: beef.bumps.length }))
}
function sortDescriptor (result) {
  return describe(() => ({ missingInputs: Array.from(result.missingInputs, String),
    notValid: Array.from(result.notValid, String), valid: Array.from(result.valid, String),
    withMissingInputs: Array.from(result.withMissingInputs, String),
    txidOnly: Array.from(result.txidOnly, String) }))
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function installTransaction (Original) {
  const prototype = Original.prototype
  const addInputOriginal = prototype.addInput
  const addOutputOriginal = prototype.addOutput
  const idOriginal = prototype.id
  const hashOriginal = prototype.hash
  const toUint8ArrayOriginal = prototype.toUint8Array
  const toHexOriginal = prototype.toHex
  const toBEEFBytesOriginal = prototype.toBEEFBytes
  const toBEEFUint8ArrayOriginal = prototype.toBEEFUint8Array
  const toAtomicBEEFUint8ArrayOriginal = prototype.toAtomicBEEFUint8Array
  const verifyOriginal = prototype.verify
  const signOriginal = prototype.sign
  const fromHexOriginal = Original.fromHex
  const fromAtomicBEEFOriginal = Original.fromAtomicBEEF
  const fromAtomicBEEFViewOriginal = Original.fromAtomicBEEFView

  prototype.addInput = function (...args) {
    return observe('addInput', [inputDescriptor(args[0])],
      () => Reflect.apply(addInputOriginal, this, args), voidResult)
  }
  prototype.addOutput = function (...args) {
    return observe('addOutput', [outputDescriptor(args[0])],
      () => Reflect.apply(addOutputOriginal, this, args), voidResult)
  }
  prototype.id = function (...args) {
    return observe('id', args.length === 0 ? [] : [args[0]],
      () => Reflect.apply(idOriginal, this, args), result => result)
  }
  prototype.hash = function (...args) {
    return observe('hash', args.length === 0 ? [] : [args[0]],
      () => Reflect.apply(hashOriginal, this, args),
      result => Array.isArray(result) ? blob('hash', hex(result)) : result)
  }
  prototype.toUint8Array = function (...args) {
    return observe('toUint8Array', [], () => Reflect.apply(toUint8ArrayOriginal, this, args),
      result => bytesBlob('bytes', result))
  }
  prototype.toHex = function (...args) {
    return observe('toHex', [], () => Reflect.apply(toHexOriginal, this, args),
      result => blob('hex', result))
  }
  prototype.toBEEFBytes = function (...args) {
    return observeThrow('toBEEFBytes', [], () => Reflect.apply(toBEEFBytesOriginal, this, args),
      result => bytesBlob('bytes', result))
  }
  prototype.toBEEFUint8Array = function (...args) {
    return observe('toBEEFUint8Array', [], () => Reflect.apply(toBEEFUint8ArrayOriginal, this, args),
      result => bytesBlob('numberArray', result))
  }
  prototype.toAtomicBEEFUint8Array = function (...args) {
    return observe('toAtomicBEEFUint8Array', [], () => Reflect.apply(toAtomicBEEFUint8ArrayOriginal, this, args),
      result => bytesBlob('bytes', result))
  }
  prototype.verify = function (...args) {
    if (depth !== 0) return Reflect.apply(verifyOriginal, this, args)
    return observeAsync('verify', args.length === 0 ? [] : [args[0]],
      () => Reflect.apply(verifyOriginal, this, args), result => result)
  }
  prototype.sign = function (...args) {
    if (depth !== 0) return Reflect.apply(signOriginal, this, args)
    return observeAsync('sign', [], () => Reflect.apply(signOriginal, this, args), voidResult)
  }
  Original.fromHex = function (...args) {
    if (depth !== 0) return Reflect.apply(fromHexOriginal, Original, args)
    return observe('fromHex', args.map(value => blob('hex', String(value))),
      () => Reflect.apply(fromHexOriginal, Original, args), txDescriptor)
  }
  Original.fromAtomicBEEF = function (...args) {
    if (depth !== 0) return Reflect.apply(fromAtomicBEEFOriginal, Original, args)
    return observeThrow('fromAtomicBEEF', args.map(value => bytesBlob('bytes', value)),
      () => Reflect.apply(fromAtomicBEEFOriginal, Original, args), txDescriptor)
  }
  Original.fromAtomicBEEFView = function (...args) {
    if (depth !== 0) return Reflect.apply(fromAtomicBEEFViewOriginal, Original, args)
    return observeThrow('fromAtomicBEEFView', args.map(value => bytesBlob('bytes', value)),
      () => Reflect.apply(fromAtomicBEEFViewOriginal, Original, args), txDescriptor)
  }
}

function installBeef (Original) {
  const prototype = Original.prototype
  const toUint8ArrayOriginal = prototype.toUint8Array
  const toUint8ArrayAtomicOriginal = prototype.toUint8ArrayAtomic
  const toWriterOriginal = prototype.toWriter
  const isValidOriginal = prototype.isValid
  const isAtomicOriginal = prototype.isAtomic
  const findAtomicTransactionOriginal = prototype.findAtomicTransaction
  const findBumpOriginal = prototype.findBump
  const mergeRawTxOriginal = prototype.mergeRawTx
  const mergeBumpOriginal = prototype.mergeBump
  const mergeTransactionOriginal = prototype.mergeTransaction
  const sortTxsOriginal = prototype.sortTxs
  const removeExistingTxidOriginal = prototype.removeExistingTxid
  const fromBinaryOriginal = Original.fromBinary
  const fromBinaryViewOriginal = Original.fromBinaryView

  prototype.toUint8Array = function (...args) {
    return observe('toUint8Array', [], () => Reflect.apply(toUint8ArrayOriginal, this, args),
      result => bytesBlob('bytes', result))
  }
  prototype.toUint8ArrayAtomic = function (...args) {
    return observe('toUint8ArrayAtomic', [args[0]],
      () => Reflect.apply(toUint8ArrayAtomicOriginal, this, args),
      result => bytesBlob('bytes', result))
  }
  prototype.toWriter = function (...args) {
    if (depth !== 0 || !calledFromTest()) return Reflect.apply(toWriterOriginal, this, args)
    depth++
    try {
      const result = Reflect.apply(toWriterOriginal, this, args)
      // 原测试序列化后直接取 writer 字节；这里登记同一 writer 的最终字节。
      record('toWriter', [], describe(() => bytesBlob('bytes', args[0].toUint8Array())))
      return result
    } finally {
      depth--
    }
  }
  prototype.isValid = function (...args) {
    if (depth !== 0) return Reflect.apply(isValidOriginal, this, args)
    return observe('isValid', args.length === 0 ? [] : [args[0]],
      () => Reflect.apply(isValidOriginal, this, args), result => result)
  }
  prototype.isAtomic = function (...args) {
    if (depth !== 0) return Reflect.apply(isAtomicOriginal, this, args)
    return observe('isAtomic', args.length === 0 ? [] : [args[0]],
      () => Reflect.apply(isAtomicOriginal, this, args), result => result)
  }
  prototype.findAtomicTransaction = function (...args) {
    if (depth !== 0) return Reflect.apply(findAtomicTransactionOriginal, this, args)
    return observe('findAtomicTransaction', [args[0]],
      () => Reflect.apply(findAtomicTransactionOriginal, this, args),
      result => result === undefined || result === null ? null : { txid: describe(() => result.id('hex')) })
  }
  prototype.findBump = function (...args) {
    if (depth !== 0) return Reflect.apply(findBumpOriginal, this, args)
    return observe('findBump', [args[0]],
      () => Reflect.apply(findBumpOriginal, this, args),
      result => result === undefined ? null : pathDescriptor(result))
  }
  prototype.mergeRawTx = function (...args) {
    return observe('mergeRawTx', [bytesBlob('bytes', args[0]), args.length > 1 ? jsNumber(args[1]) : null],
      () => Reflect.apply(mergeRawTxOriginal, this, args), beefTxDescriptor)
  }
  prototype.mergeBump = function (...args) {
    return observe('mergeBump', [pathDescriptor(args[0])],
      () => Reflect.apply(mergeBumpOriginal, this, args), result => jsNumber(result))
  }
  prototype.mergeTransaction = function (...args) {
    return observe('mergeTransaction', [txDescriptor(args[0])],
      () => Reflect.apply(mergeTransactionOriginal, this, args), beefTxDescriptor)
  }
  prototype.sortTxs = function (...args) {
    return observe('sortTxs', [], () => Reflect.apply(sortTxsOriginal, this, args), sortDescriptor)
  }
  prototype.removeExistingTxid = function (...args) {
    return observe('removeExistingTxid', [args[0]],
      () => Reflect.apply(removeExistingTxidOriginal, this, args), voidResult)
  }
  Original.fromBinary = function (...args) {
    if (depth !== 0) return Reflect.apply(fromBinaryOriginal, Original, args)
    return observeThrow('fromBinary', [bytesBlob('bytes', args[0])],
      () => Reflect.apply(fromBinaryOriginal, Original, args), beefDescriptor)
  }
  Original.fromBinaryView = function (...args) {
    if (depth !== 0) return Reflect.apply(fromBinaryViewOriginal, Original, args)
    return observeThrow('fromBinaryView', [bytesBlob('bytes', args[0])],
      () => Reflect.apply(fromBinaryViewOriginal, Original, args), beefDescriptor)
  }
}

function installBeefTx (Original) {
  const fromRawTxOriginal = Original.fromRawTx
  Original.fromRawTx = function (...args) {
    if (depth !== 0) return Reflect.apply(fromRawTxOriginal, Original, args)
    const descriptor = [bytesBlob('bytes', args[0])]
    if (args.length > 1 && args[1] !== undefined) descriptor.push(jsNumber(args[1]))
    return observe('fromRawTx', descriptor, () => Reflect.apply(fromRawTxOriginal, Original, args),
      beefTxDescriptor)
  }
}

jest.doMock(transactionModulePath, () => {
  const moduleObject = jest.requireActual(transactionModulePath)
  if (transactionInstalled || moduleObject.default === undefined) return moduleObject
  transactionInstalled = true
  installTransaction(moduleObject.default)
  return moduleObject
})
jest.doMock(beefModulePath, () => {
  const moduleObject = jest.requireActual(beefModulePath)
  if (beefInstalled || moduleObject.default === undefined) return moduleObject
  beefInstalled = true
  installBeef(moduleObject.default)
  return moduleObject
})
jest.doMock(beefTxModulePath, () => {
  const moduleObject = jest.requireActual(beefTxModulePath)
  if (beefTxInstalled || moduleObject.default === undefined) return moduleObject
  beefTxInstalled = true
  installBeefTx(moduleObject.default)
  return moduleObject
})
