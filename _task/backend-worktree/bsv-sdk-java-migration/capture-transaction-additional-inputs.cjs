// 固定 Transaction.additional.test.ts 原输入：解析入口、增入/增出、哈希、id、AtomicBEEF、费用、签名与序列化。
// Transaction 与 Beef 互相引用，因此用真实模块只包装原型/静态方法，避免 jest.doMock 的循环加载。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_TRANSACTION_ADDITIONAL_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Transaction additional 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/Transaction.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  // 异步回调里栈已经不含原测试帧；行号只作说明，样本身份用入口名与序号。
  const match = new Error().stack.match(/Transaction\.additional\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('Transaction additional 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function observe (method, args, action, describe) {
  if (depth !== 0) return action()
  depth++
  try {
    const result = action()
    record(method, args, describe === undefined ? null : describe(result))
    return result
  } catch (error) {
    record(method, args, thrown(error))
    throw error
  } finally {
    depth--
  }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function jsNumber (value) {
  return Number.isInteger(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER ? value : String(value)
}
function describeScript (script) {
  if (script === null || script === undefined) return null
  return { asm: script.toASM(), hex: script.toHex() }
}
function describeInputArg (item) {
  return { sourceTXID: item.sourceTXID ?? null,
    sourceOutputIndex: jsNumber(item.sourceOutputIndex ?? 0),
    unlockingScript: describeScript(item.unlockingScript),
    sequence: item.sequence === undefined ? null : jsNumber(item.sequence),
    hasTemplate: typeof item.unlockingScriptTemplate === 'object' && item.unlockingScriptTemplate !== null,
    hasSourceTransaction: typeof item.sourceTransaction === 'object' && item.sourceTransaction !== null }
}
function describeOutputArg (item) {
  return { satoshis: item.satoshis === undefined ? null : jsNumber(item.satoshis),
    lockingScript: describeScript(item.lockingScript),
    change: item.change === undefined ? null : item.change }
}
function describeTransaction (tx) {
  return { kind: 'transaction', inputs: tx.inputs.length, outputs: tx.outputs.length }
}
function describeBytes (bytes) { return { kind: 'bytes', hex: hex(bytes) } }
function describeNumberArray (values) {
  return { kind: 'numberArray', hex: hex(Uint8Array.from(values)), length: values.length }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function install (Original) {
  const originals = {}
  for (const method of ['addInput', 'addOutput', 'addP2PKHOutput', 'hash', 'id', 'toHexAtomicBEEF', 'getFee',
    'sign', 'toEF', 'toBinary']) originals[method] = Original.prototype[method]
  for (const method of ['fromHexEF', 'fromAtomicBEEF', 'fromAtomicBEEFView', 'fromEF']) originals[method] = Original[method]

  Original.prototype.addInput = function (...args) {
    return observe('addInput', [describeInputArg(args[0])],
      () => Reflect.apply(originals.addInput, this, args), () => describeTransaction(this))
  }
  Original.prototype.addOutput = function (...args) {
    return observe('addOutput', [describeOutputArg(args[0])],
      () => Reflect.apply(originals.addOutput, this, args), () => describeTransaction(this))
  }
  Original.prototype.addP2PKHOutput = function (...args) {
    return observe('addP2PKHOutput', [{ kind: 'array', value: Array.from(args[0]) }],
      () => Reflect.apply(originals.addP2PKHOutput, this, args), () => describeTransaction(this))
  }
  Original.prototype.hash = function (...args) {
    return observe('hash', args.map(value => value ?? null),
      () => Reflect.apply(originals.hash, this, args), result => ({ kind: 'string', value: result }))
  }
  Original.prototype.id = function (...args) {
    return observe('id', args.map(value => value ?? null), () => Reflect.apply(originals.id, this, args),
      result => (typeof result === 'string' ? { kind: 'string', value: result } : describeNumberArray(result)))
  }
  Original.prototype.toHexAtomicBEEF = function (...args) {
    return observe('toHexAtomicBEEF', [],
      () => Reflect.apply(originals.toHexAtomicBEEF, this, args), result => ({ kind: 'string', value: result }))
  }
  Original.prototype.getFee = function (...args) {
    return observe('getFee', [], () => Reflect.apply(originals.getFee, this, args),
      result => ({ kind: 'number', value: String(result) }))
  }
  Original.prototype.sign = function (...args) {
    const line = callLine()
    const options = args[0] === undefined ? null : { skipExistingSignatures: args[0].skipExistingSignatures === true }
    if (depth !== 0) return Reflect.apply(originals.sign, this, args)
    depth++
    return Promise.resolve(Reflect.apply(originals.sign, this, args)).then(result => {
      try { record('sign', [options], null, line); return result } finally { depth-- }
    }, error => {
      try { record('sign', [options], thrown(error), line); throw error } finally { depth-- }
    })
  }
  Original.prototype.toEF = function (...args) {
    return observe('toEF', [], () => Reflect.apply(originals.toEF, this, args), describeBytes)
  }
  Original.prototype.toBinary = function (...args) {
    return observe('toBinary', [], () => Reflect.apply(originals.toBinary, this, args), describeBytes)
  }
  Original.fromHexEF = function (...args) {
    return observe('fromHexEF', [args[0]], () => Reflect.apply(originals.fromHexEF, this, args), describeTransaction)
  }
  for (const method of ['fromAtomicBEEF', 'fromAtomicBEEFView', 'fromEF']) {
    Original[method] = function (...args) {
      return observe(method, [describeBytes(args[0])],
        () => Reflect.apply(originals[method], this, args), describeTransaction)
    }
  }
}

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  install(moduleObject.default)
  return moduleObject
})
