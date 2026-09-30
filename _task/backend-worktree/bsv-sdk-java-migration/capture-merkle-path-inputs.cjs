// 固定 MerklePath.test.ts 原输入：构造入参、computeRoot／toHex／toBinary 结果、
// extract／combine／findOrComputeLeaf／verify 与 fromHex／fromBinary／fromCoinbaseTxidAndHeight 的真实入口。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_MERKLE_PATH_TS_OBSERVATIONS
if (!output) throw new Error('缺少 MerklePath 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/MerklePath.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let constructing = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/MerklePath\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('MerklePath 入口缺少固定原测试调用位置')
  return Number(match[1])
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('MerklePath 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function observe (method, args, action, describe) {
  if (depth !== 0 || constructing !== 0) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? result : describe(result))
    return result
  } finally {
    depth--
  }
}
// 描述参数时调用的公开方法算内部调用，不另记入口。
function describe (build) {
  depth++
  try {
    return build()
  } finally {
    depth--
  }
}
// 原测试用到 NaN／Infinity／超出 2^53-1 的 offset，按 JS Number 语义无损登记。
function numberLiteral (value) {
  if (typeof value !== 'number') return value
  if (Number.isNaN(value)) return 'NaN'
  if (value === Infinity) return 'Infinity'
  if (value === -Infinity) return '-Infinity'
  if (Number.isInteger(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER) return value
  return String(value)
}
function describeLeaf (leaf) {
  const out = { offset: numberLiteral(leaf.offset) }
  if (leaf.hash !== undefined) out.hash = leaf.hash
  if (leaf.txid !== undefined) out.txid = leaf.txid
  if (leaf.duplicate !== undefined) out.duplicate = leaf.duplicate
  return out
}
function describePath (levels) { return levels.map(level => level.map(describeLeaf)) }
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function describeThrown (error) {
  return { kind: 'throw', name: error.constructor ? error.constructor.name : String(error),
    message: String(error.message) }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  const MerklePath = moduleObject.default
  const computeRootOriginal = MerklePath.prototype.computeRoot
  const toHexOriginal = MerklePath.prototype.toHex
  const findOrComputeLeafOriginal = MerklePath.prototype.findOrComputeLeaf
  const extractOriginal = MerklePath.prototype.extract
  const combineOriginal = MerklePath.prototype.combine
  const toBinaryOriginal = MerklePath.prototype.toBinary
  const verifyOriginal = MerklePath.prototype.verify
  const toBinaryUint8ArrayOriginal = MerklePath.prototype.toBinaryUint8Array
  const fromHexOriginal = MerklePath.fromHex
  const fromCoinbaseTxidAndHeightOriginal = MerklePath.fromCoinbaseTxidAndHeight
  const fromBinaryOriginal = MerklePath.fromBinary
  MerklePath.prototype.computeRoot = function (...args) {
    return observe('computeRoot', [args[0] ?? null], () => Reflect.apply(computeRootOriginal, this, args),
      result => ({ kind: 'string', value: result }))
  }
  MerklePath.prototype.toHex = function (...args) {
    return observe('toHex', [], () => Reflect.apply(toHexOriginal, this, args),
      result => ({ kind: 'bytes', hex: result }))
  }
  MerklePath.prototype.findOrComputeLeaf = function (...args) {
    return observe('findOrComputeLeaf', [args[0], numberLiteral(args[1])],
      () => Reflect.apply(findOrComputeLeafOriginal, this, args),
      result => result == null ? null : describeLeaf(result))
  }
  MerklePath.prototype.extract = function (...args) {
    // 原测试有 extract 抛异常的用例（空 txid 列表／未知 txid），异常观测同样进样本。
    if (depth !== 0 || constructing !== 0 || !current()) return Reflect.apply(extractOriginal, this, args)
    const targets = Array.from(args[0])
    depth++
    try {
      const result = Reflect.apply(extractOriginal, this, args)
      record('extract', [targets], { kind: 'bytes', hex: result.toHex() })
      return result
    } catch (error) {
      record('extract', [targets], describeThrown(error))
      throw error
    } finally {
      depth--
    }
  }
  MerklePath.prototype.combine = function (...args) {
    const other = args[0] == null ? null : describe(() => args[0].toHex())
    // 原测试有 combine 抛异常的用例（block height／root 不一致），异常观测同样进样本。
    if (depth !== 0 || constructing !== 0 || !current()) return Reflect.apply(combineOriginal, this, args)
    depth++
    try {
      const result = Reflect.apply(combineOriginal, this, args)
      record('combine', [other], null)
      return result
    } catch (error) {
      record('combine', [other], describeThrown(error))
      throw error
    } finally {
      depth--
    }
  }
  MerklePath.prototype.toBinary = function (...args) {
    return observe('toBinary', [], () => Reflect.apply(toBinaryOriginal, this, args),
      result => ({ kind: 'numberArray', hex: hex(result), length: result.length }))
  }
  MerklePath.prototype.verify = function (...args) {
    if (depth !== 0 || constructing !== 0 || !current()) return Reflect.apply(verifyOriginal, this, args)
    depth++
    return Promise.resolve(Reflect.apply(verifyOriginal, this, args)).then(result => {
      try {
        record('verify', [args[0] ?? null], result)
      } finally {
        depth--
      }
      return result
    }, error => {
      try {
        record('verify', [args[0] ?? null], describeThrown(error))
      } finally {
        depth--
      }
      throw error
    })
  }
  MerklePath.prototype.toBinaryUint8Array = function (...args) {
    return observe('toBinaryUint8Array', [], () => Reflect.apply(toBinaryUint8ArrayOriginal, this, args),
      result => ({ kind: 'bytes', hex: hex(result) }))
  }
  MerklePath.fromHex = function (...args) {
    // 非法 BUMP 用例要求登记原测试真实收到的解析异常。
    if (depth !== 0 || constructing !== 0 || !current()) return Reflect.apply(fromHexOriginal, MerklePath, args)
    depth++
    try {
      const result = Reflect.apply(fromHexOriginal, MerklePath, args)
      record('fromHex', [args[0]], { kind: 'bytes', hex: result.toHex() })
      return result
    } catch (error) {
      record('fromHex', [args[0]], describeThrown(error))
      throw error
    } finally {
      depth--
    }
  }
  MerklePath.fromCoinbaseTxidAndHeight = function (...args) {
    return observe('fromCoinbaseTxidAndHeight', [args[0], numberLiteral(args[1])],
      () => Reflect.apply(fromCoinbaseTxidAndHeightOriginal, MerklePath, args),
      result => ({ kind: 'bytes', hex: result.toHex() }))
  }
  MerklePath.fromBinary = function (...args) {
    const descriptor = [hex(args[0]), args[1] === undefined ? true : args[1], args[2] === undefined ? true : args[2]]
    if (depth !== 0 || constructing !== 0) return Reflect.apply(fromBinaryOriginal, MerklePath, args)
    depth++
    try {
      const result = Reflect.apply(fromBinaryOriginal, MerklePath, args)
      record('fromBinary', descriptor, { kind: 'bytes', hex: result.toHex() })
      return result
    } catch (error) {
      record('fromBinary', descriptor, describeThrown(error))
      throw error
    } finally {
      depth--
    }
  }
  // 构造期内部调用（validateRoots 会算根）不计入口，只记原测试的 new。
  const wrapped = new Proxy(MerklePath, {
    construct (target, args, newTarget) {
      const descriptor = [numberLiteral(args[0]), describePath(args[1]),
        args[2] === undefined ? true : args[2], args[3] === undefined ? true : args[3]]
      constructing++
      try {
        const instance = Reflect.construct(target, args, newTarget)
        record('constructor', descriptor, null)
        return instance
      } catch (error) {
        record('constructor', descriptor, describeThrown(error))
        throw error
      } finally {
        constructing--
      }
    }
  })
  return { ...moduleObject, default: wrapped, __esModule: true }
})
