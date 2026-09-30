// 固定 Beef.test.ts 原输入：Beef／BeefTx／MerklePath 的构造入参、公开入口实参、返回值与真实异常。
// Beef 与 Transaction／BeefTx／MerklePath 互相引用，因此用真实模块只包装原型与静态方法，
// 构造入口用 Promise 无关的 Proxy 记录；jest.doMock 只安装一次。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_BEEF_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Beef 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const beefModulePath = path.join(sdk, 'src/transaction/Beef.ts')
const beefTxModulePath = path.join(sdk, 'src/transaction/BeefTx.ts')
const merklePathModulePath = path.join(sdk, 'src/transaction/MerklePath.ts')
let Beef, BeefTx, MerklePath
let installed = false

// 返回 null 的入口（void／被丢弃的返回值）也用函数描述，避免与“没有描述函数”混淆。
const voidResult = () => null
const occurrences = new Map()
let occurrence = 0
let sequence = 0
// 非 0 表示正在执行 Java 侧同样不可观测的内部调用（静态解析、入参描述、构造期内部方法）。
let depth = 0

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/Beef\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('Beef 入口缺少固定原测试调用位置')
  return Number(match[1])
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('Beef 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function observe (method, args, action, describe) {
  if (depth !== 0) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? result : describe(result))
    return result
  } finally {
    depth--
  }
}
// 原测试自己写的 new 才算入口；静态解析（Beef.fromReader）与包装方法内部的 new 都不可观测。
function observeConstruction (method, args, action) {
  if (depth !== 0) return action()
  depth++
  try {
    const result = action()
    record(method, args, voidResult())
    return result
  } catch (error) {
    record(method, args, describeThrown(error))
    throw error
  } finally {
    depth--
  }
}
// 描述参数与返回值时调用的公开方法算内部调用，不另记入口。
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
// 原测试用到超出 32 位的数字（版本号、sequence），按 JS Number 语义无损登记。
function jsNumber (value) {
  if (typeof value !== 'number') return value
  if (Number.isInteger(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER) return value
  return String(value)
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
// 调用方传入的 MerklePath 只登记 offset/hash：TS 的合并会把 groups.paths[0]（即调用方对象）
// 就地改写，从而给它的叶子补上 txid 标志，而 Java 为新路径建新列表、不改调用方对象。
// 这属实现细节（上游用例只断言批量合并与顺序合并的字节相等与 isValid），故输入侧不比较该标志；
// Beef 自身 bumps 里的叶子仍逐值比较 txid（见 includeTxid 默认值）。
function leafDescriptor (leaf, includeTxid = true) {
  const out = { offset: jsNumber(leaf.offset) }
  if (leaf.hash !== undefined) out.hash = leaf.hash
  if (includeTxid && leaf.txid !== undefined) out.txid = leaf.txid
  if (leaf.duplicate !== undefined) out.duplicate = leaf.duplicate
  return out
}
function pathDescriptor (merklePath) {
  return describe(() => ({
    blockHeight: jsNumber(merklePath.blockHeight),
    path: merklePath.path.map(level => level.map(leaf => leafDescriptor(leaf, false)))
  }))
}
function entryDescriptor (entry) {
  const out = { rawTx: entry.rawTx === undefined || entry.rawTx === null ? null : hex(entry.rawTx),
    merklePath: entry.merklePath === undefined || entry.merklePath === null
      ? null : pathDescriptor(entry.merklePath) }
  if (entry.merkleRoot !== undefined) out.merkleRoot = entry.merkleRoot ?? null
  return out
}
function txDescriptor (value) {
  if (value === undefined || value === null) return null
  if (typeof value.id !== 'function') return null
  return describe(() => value.id('hex'))
}
function beefTxId (value) {
  if (value === undefined || value === null) return null
  return describe(() => value.txid)
}
function strings (values) {
  return describe(() => Array.from(values, value => String(value)))
}
function sortDescriptor (result) {
  return { missingInputs: strings(result.missingInputs), notValid: strings(result.notValid),
    valid: strings(result.valid), withMissingInputs: strings(result.withMissingInputs),
    txidOnly: strings(result.txidOnly) }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function installBeef (moduleObject) {
  const Original = moduleObject.default
  const prototype = Original.prototype
  const toHexOriginal = prototype.toHex
  const toBinaryOriginal = prototype.toBinary
  const toLogStringOriginal = prototype.toLogString
  const isValidOriginal = prototype.isValid
  const verifyOriginal = prototype.verify
  const sortTxsOriginal = prototype.sortTxs
  const partitionTxsOriginal = prototype.partitionTxs
  const mergeTransactionOriginal = prototype.mergeTransaction
  const mergeBumpOriginal = prototype.mergeBump
  const mergeRawTxOriginal = prototype.mergeRawTx
  const mergeProvenTxsOriginal = prototype.mergeProvenTxs
  const mergeTxidOnlyOriginal = prototype.mergeTxidOnly
  const mergeBeefOriginal = prototype.mergeBeef
  const removeExistingTxidOriginal = prototype.removeExistingTxid
  const trimKnownTxidsOriginal = prototype.trimKnownTxids
  const makeTxidOnlyOriginal = prototype.makeTxidOnly
  const findTransactionForSigningOriginal = prototype.findTransactionForSigning
  const findAtomicTransactionOriginal = prototype.findAtomicTransaction
  const toBinaryAtomicOriginal = prototype.toBinaryAtomic
  const toUint8ArrayAtomicOriginal = prototype.toUint8ArrayAtomic
  const addComputedLeavesOriginal = prototype.addComputedLeaves
  const fromStringOriginal = Original.fromString
  const fromBinaryOriginal = Original.fromBinary

  // 返回原始对象的方法：返回值和上游一致，只是调用点全部登记。
  prototype.toHex = function (...args) {
    return observe('toHex', [], () => Reflect.apply(toHexOriginal, this, args),
      result => ({ kind: 'string', value: result }))
  }
  prototype.toBinary = function (...args) {
    return observe('toBinary', [], () => Reflect.apply(toBinaryOriginal, this, args),
      result => ({ kind: 'numberArray', hex: hex(result), length: result.length }))
  }
  prototype.toLogString = function (...args) {
    return observe('toLogString', [], () => Reflect.apply(toLogStringOriginal, this, args),
      result => ({ kind: 'string', value: result }))
  }
  prototype.isValid = function (...args) {
    if (depth !== 0) return Reflect.apply(isValidOriginal, this, args)
    const descriptor = [args[0] === undefined ? null : args[0]]
    depth++
    try {
      const result = Reflect.apply(isValidOriginal, this, args)
      record('isValid', descriptor, result)
      return result
    } catch (error) {
      record('isValid', descriptor, describeThrown(error))
      throw error
    } finally {
      depth--
    }
  }
  prototype.verify = function (...args) {
    if (depth !== 0) return Reflect.apply(verifyOriginal, this, args)
    const descriptor = [args[0] ?? null, args[1] === undefined ? null : args[1]]
    depth++
    return Promise.resolve(Reflect.apply(verifyOriginal, this, args)).then(result => {
      try {
        record('verify', descriptor, result)
      } finally {
        depth--
      }
      return result
    }, error => {
      try {
        record('verify', descriptor, describeThrown(error))
      } finally {
        depth--
      }
      throw error
    })
  }
  prototype.sortTxs = function (...args) {
    return observe('sortTxs', [], () => Reflect.apply(sortTxsOriginal, this, args), sortDescriptor)
  }
  // 原测试用 spyOn 观察内部划分调用次数，因此同样登记且不省略。
  prototype.partitionTxs = function (...args) {
    if (depth !== 0) return Reflect.apply(partitionTxsOriginal, this, args)
    return observe('partitionTxs', [], () => Reflect.apply(partitionTxsOriginal, this, args), voidResult)
  }
  prototype.mergeTransaction = function (...args) {
    return observe('mergeTransaction', [txDescriptor(args[0])],
      () => Reflect.apply(mergeTransactionOriginal, this, args), beefTxId)
  }
  prototype.mergeBump = function (...args) {
    return observe('mergeBump', [args[0] == null ? null : pathDescriptor(args[0])],
      () => Reflect.apply(mergeBumpOriginal, this, args), voidResult)
  }
  prototype.mergeRawTx = function (...args) {
    const descriptor = [args[0] == null ? null : hex(args[0]), args[1] === undefined ? null : jsNumber(args[1])]
    return observe('mergeRawTx', descriptor,
      () => Reflect.apply(mergeRawTxOriginal, this, args), beefTxId)
  }
  prototype.mergeProvenTxs = function (...args) {
    return observe('mergeProvenTxs', [Array.from(args[0] ?? [], entryDescriptor)],
      () => Reflect.apply(mergeProvenTxsOriginal, this, args),
      result => strings(result.map(entry => entry.txid)))
  }
  prototype.mergeTxidOnly = function (...args) {
    return observe('mergeTxidOnly', [args[0]], () => Reflect.apply(mergeTxidOnlyOriginal, this, args), beefTxId)
  }
  prototype.mergeBeef = function (...args) {
    const incoming = args[0]
    const descriptor = incoming instanceof Uint8Array || Array.isArray(incoming)
      ? { kind: 'bytes', hex: hex(incoming) }
      : { kind: 'beef', txids: describe(() => incoming.txs.map(tx => tx.txid)) }
    return observe('mergeBeef', [descriptor], () => Reflect.apply(mergeBeefOriginal, this, args), voidResult)
  }
  prototype.removeExistingTxid = function (...args) {
    return observe('removeExistingTxid', [args[0]], () => Reflect.apply(removeExistingTxidOriginal, this, args), voidResult)
  }
  prototype.trimKnownTxids = function (...args) {
    return observe('trimKnownTxids', [Array.from(args[0] ?? [], value => String(value))],
      () => Reflect.apply(trimKnownTxidsOriginal, this, args), voidResult)
  }
  prototype.makeTxidOnly = function (...args) {
    return observe('makeTxidOnly', [args[0]], () => Reflect.apply(makeTxidOnlyOriginal, this, args), beefTxId)
  }
  prototype.findTransactionForSigning = function (...args) {
    return observe('findTransactionForSigning', [args[0]],
      () => Reflect.apply(findTransactionForSigningOriginal, this, args), txDescriptor)
  }
  prototype.findAtomicTransaction = function (...args) {
    return observe('findAtomicTransaction', [args[0]],
      () => Reflect.apply(findAtomicTransactionOriginal, this, args), txDescriptor)
  }
  prototype.toBinaryAtomic = function (...args) {
    return observe('toBinaryAtomic', [args[0]], () => Reflect.apply(toBinaryAtomicOriginal, this, args),
      result => ({ kind: 'numberArray', hex: hex(result), length: result.length }))
  }
  prototype.toUint8ArrayAtomic = function (...args) {
    return observe('toUint8ArrayAtomic', [args[0]], () => Reflect.apply(toUint8ArrayAtomicOriginal, this, args),
      result => ({ kind: 'bytes', hex: hex(result) }))
  }
  prototype.addComputedLeaves = function (...args) {
    return observe('addComputedLeaves', [], () => Reflect.apply(addComputedLeavesOriginal, this, args), voidResult)
  }
  Original.fromString = function (...args) {
    if (depth !== 0) return Reflect.apply(fromStringOriginal, Original, args)
    return observe('fromString', args[0] === undefined ? [null] : [args[0]],
      () => Reflect.apply(fromStringOriginal, Original, args),
      result => ({ kind: 'bytes', hex: describe(() => result.toHex()) }))
  }
  Original.fromBinary = function (...args) {
    if (depth !== 0) return Reflect.apply(fromBinaryOriginal, Original, args)
    return observe('fromBinary', [hex(args[0])], () => Reflect.apply(fromBinaryOriginal, Original, args),
      result => ({ kind: 'bytes', hex: describe(() => result.toHex()) }))
  }
  // 原测试只在构造期用到这些方法，但包装后能发现 Java 侧多算／少算的候选。
  const cloneOriginal = prototype.clone
  const isAtomicOriginal = prototype.isAtomic
  const getValidTxidsOriginal = prototype.getValidTxids
  prototype.clone = function (...args) {
    return observe('clone', [], () => Reflect.apply(cloneOriginal, this, args),
      result => ({ bumps: [], txs: describe(() => result.txs.map(tx => ({ inputTxids: [], _txid: tx.txid }))),
        version: result.version }))
  }
  prototype.isAtomic = function (...args) {
    return observe('isAtomic', args.length === 0 ? [] : [args[0]],
      () => Reflect.apply(isAtomicOriginal, this, args))
  }
  prototype.getValidTxids = function (...args) {
    return observe('getValidTxids', [], () => Reflect.apply(getValidTxidsOriginal, this, args), strings)
  }
  return new Proxy(Original, {
    construct (target, args, newTarget) {
      const descriptor = args.length === 0 ? [] : [jsNumber(args[0])]
      return observeConstruction('constructor', descriptor,
        () => Reflect.construct(target, args, newTarget))
    }
  })
}

// BeefTx／MerklePath 由原测试直接 new，必须同样登记，否则只构造不调方法的用例没有样本。
function installBeefTx (moduleObject) {
  const Original = moduleObject.default
  return new Proxy(Original, {
    construct (target, args, newTarget) {
      const first = args[0]
      const bytes = first instanceof Uint8Array || Array.isArray(first)
      // (transaction, bumpIndex) 只登记本位参数，避免把 bumpIndex 混进 txid 位。
      const descriptor = !bytes && typeof first !== 'string' && typeof args[1] === 'number'
        ? [txDescriptor(first), jsNumber(args[1])]
        : [first !== null && typeof first === 'object' && !bytes ? txDescriptor(first) : null,
            bytes ? hex(first) : null,
            typeof first === 'string' ? first : null]
      return observeConstruction('constructor', descriptor,
        () => Reflect.construct(target, args, newTarget))
    }
  })
}

function installMerklePath (moduleObject) {
  const Original = moduleObject.default
  return new Proxy(Original, {
    construct (target, args, newTarget) {
      // 调用方传入的路径按输入侧口径比较（不含 txid 标志），与 Java 重放一致。
      const descriptor = [jsNumber(args[0]), args[1] === undefined ? null : describe(() => args[1].map(
        level => level.map(leaf => leafDescriptor(leaf, false)))), args[2] === undefined ? null : args[2],
      args[3] === undefined ? null : args[3]]
      return observeConstruction('constructor', descriptor,
        () => Reflect.construct(target, args, newTarget))
    }
  })
}

// Beef 与 Transaction／BeefTx／MerklePath 循环引用：只包装原型与静态方法，且只安装一次。
jest.doMock(beefModulePath, () => {
  const moduleObject = jest.requireActual(beefModulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  BeefTx = require(beefTxModulePath).default
  MerklePath = require(merklePathModulePath).default
  Beef = installBeef(moduleObject)
  return { ...moduleObject, default: Beef, __esModule: true }
})
jest.doMock(beefTxModulePath, () => {
  const moduleObject = jest.requireActual(beefTxModulePath)
  if (moduleObject.default === undefined) return moduleObject
  return { ...moduleObject, default: installBeefTx(moduleObject), __esModule: true }
})
jest.doMock(merklePathModulePath, () => {
  const moduleObject = jest.requireActual(merklePathModulePath)
  if (moduleObject.default === undefined) return moduleObject
  return { ...moduleObject, default: installMerklePath(moduleObject), __esModule: true }
})
