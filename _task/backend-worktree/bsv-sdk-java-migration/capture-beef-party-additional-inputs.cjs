// 固定 BeefParty.additional.test.ts 原输入：Beef／BeefParty 的真实入口实参、二进制与 txid 结果。
// BeefParty 继承 Beef 且两者互相引用，因此用真实模块只包装原型方法，避免 jest.doMock 的循环加载。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_BEEF_PARTY_ADDITIONAL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 BeefParty 补充用例原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const beefModule = path.join(sdk, 'src/transaction/Beef.ts')
const partyModule = path.join(sdk, 'src/transaction/BeefParty.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let constructing = 0
let beefInstalled = false
let partyInstalled = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/BeefParty\.additional\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('BeefParty 补充用例入口缺少固定原测试调用位置')
  return Number(match[1])
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('BeefParty 补充用例入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function observe (method, args, action, describe) {
  // 构造期间的内部 isParty（原测试只写 new BeefParty([...])）不属于原测试入口。
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
// 描述内部再调用被包装的公开方法（getValidTxids）时按内部调用处理，不另记入口。
function describe (build) {
  depth++
  try {
    return build()
  } finally {
    depth--
  }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function describeBeef (beef) {
  if (beef instanceof Uint8Array || Array.isArray(beef)) return { kind: 'bytes', hex: hex(beef) }
  return { kind: 'beef', txids: Array.from(beef.getValidTxids()) }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(beefModule, () => {
  const moduleObject = jest.requireActual(beefModule)
  if (beefInstalled || moduleObject.Beef === undefined) return moduleObject
  beefInstalled = true
  const Beef = moduleObject.Beef
  const mergeTransactionOriginal = Beef.prototype.mergeTransaction
  const getValidTxidsOriginal = Beef.prototype.getValidTxids
  const toBinaryOriginal = Beef.prototype.toBinary
  const isValidOriginal = Beef.prototype.isValid
  Beef.prototype.mergeTransaction = function (...args) {
    return observe('mergeTransaction',
      [{ kind: 'transaction', txid: args[0].id('hex') }],
      () => Reflect.apply(mergeTransactionOriginal, this, args), () => null)
  }
  Beef.prototype.getValidTxids = function (...args) {
    return observe('getValidTxids', [],
      () => Reflect.apply(getValidTxidsOriginal, this, args),
      result => ({ kind: 'strings', values: Array.from(result) }))
  }
  Beef.prototype.toBinary = function (...args) {
    return observe('toBinary', [], () => Reflect.apply(toBinaryOriginal, this, args),
      result => ({ kind: 'bytes', hex: hex(result) }))
  }
  Beef.prototype.isValid = function (...args) {
    return observe('isValid', [], () => Reflect.apply(isValidOriginal, this, args))
  }
  return moduleObject
})

jest.doMock(partyModule, () => {
  const moduleObject = jest.requireActual(partyModule)
  if (partyInstalled || moduleObject.default === undefined) return moduleObject
  partyInstalled = true
  const BeefParty = moduleObject.default
  const mergeBeefFromPartyOriginal = BeefParty.prototype.mergeBeefFromParty
  const isPartyOriginal = BeefParty.prototype.isParty
  const getKnownTxidsForPartyOriginal = BeefParty.prototype.getKnownTxidsForParty
  BeefParty.prototype.mergeBeefFromParty = function (...args) {
    const known = describe(() => describeBeef(args[1]))
    return observe('mergeBeefFromParty', [args[0], known],
      () => Reflect.apply(mergeBeefFromPartyOriginal, this, args), () => null)
  }
  BeefParty.prototype.isParty = function (...args) {
    return observe('isParty', [args[0]], () => Reflect.apply(isPartyOriginal, this, args))
  }
  BeefParty.prototype.getKnownTxidsForParty = function (...args) {
    return observe('getKnownTxidsForParty', [args[0]],
      () => Reflect.apply(getKnownTxidsForPartyOriginal, this, args),
      result => ({ kind: 'strings', values: Array.from(result) }))
  }
  // 构造只用于抑制构造期内部调用，不记入口；原型仍指向真实类，instanceof 不变。
  const wrapped = new Proxy(BeefParty, {
    construct (target, args, newTarget) {
      constructing++
      try {
        return Reflect.construct(target, args, newTarget)
      } finally {
        constructing--
      }
    }
  })
  return { ...moduleObject, default: wrapped, __esModule: true }
})
