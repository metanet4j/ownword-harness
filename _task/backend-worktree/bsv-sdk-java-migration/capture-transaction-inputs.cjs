// 固定 Transaction.test.ts 61 条非向量用例的原输入：构造、解析、序列化、hash/txid、
// 费用、签名、广播、验证、preimage 与钱包补全的实参与结果逐值记录。
//
// 该文件同时承载 659 条向量用例（transaction-shared-vectors 专用局部），探针只记录本局部
// 计划内的用例，避免把向量轨迹混进本局部。Transaction 与 Beef 互相引用，因此不改模块工厂，
// 只包装真实类的原型/静态方法并用构造函数 Proxy 记录 `constructor`；安装一次，重入时直接返回。
//
// 固定随机：preventResourceExhaustionP2PKH 原用例用 PrivateKey.fromRandom()，探针在采集期把
// 该静态入口固定为 PrivateKey(1)（与既有 Java 用例一致），使随机密钥也不产生不可比对的字节。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_TRANSACTION_TS_OBSERVATIONS
if (!output) throw new Error('缺少 Transaction 原输入采集路径')
const task = __dirname
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/Transaction.ts')
const privateKeyPath = path.join(sdk, 'src/primitives/PrivateKey.ts')
const VECTORS_CLASS = 'com.metanet4j.bsv.transaction.TransactionCompleteVectorsTest'

const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false
let keyInstalled = false

function allowedTests () {
  const catalog = JSON.parse(fs.readFileSync(path.join(task, 'module-tests.json'), 'utf8'))
  const mapping = JSON.parse(fs.readFileSync(path.join(task, 'test-map.json'), 'utf8'))
  const source = catalog.files.find(file => file.path === sourceFile)
  if (!source) throw new Error('探针来源不在冻结清单：' + sourceFile)
  const planPath = process.env.EVIDENCE_INPUT_PLAN
  const planned = planPath && fs.existsSync(planPath)
    ? new Set(Object.keys(JSON.parse(fs.readFileSync(planPath, 'utf8'))))
    : null
  const byId = new Map(mapping.cases.map(item => [item.id, item]))
  const tests = source.cases.filter(item => {
    if (planned) return planned.has(item.id)
    return byId.get(item.id).java[0].className !== VECTORS_CLASS
  }).map(item => item.names.join(' '))
  if (tests.length === 0) throw new Error('Transaction 原输入采集未解析出用例：' + sourceFile)
  return new Set(tests)
}

const allowed = allowedTests()

function current () { return expect.getState().currentTestName }
function recording () { return allowed.has(current()) }
function callLine () {
  const match = new Error().stack.match(/Transaction\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
// 只记录原测试自己发起的构造：SDK 内部（如 compat/Utxo 的 fromUtxo）借同一模块 new 出的
// Transaction 不属于原测试的公开入口，Java 侧的内部构造不经过重放，两侧必须同样忽略。
function calledFromTest () {
  const stack = (new Error().stack || '').split('\n').slice(1)
  for (const line of stack) {
    if (line.includes('capture-transaction-inputs.cjs')) continue
    return line.includes('Transaction.test.ts')
  }
  return false
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('Transaction 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function observe (method, args, action, describe) {
  const top = depth === 0
  if (!top) return action()
  depth++
  try {
    const result = action()
    if (recording()) record(method, args, describe === undefined ? null : describe(result))
    return result
  } catch (error) {
    if (recording()) record(method, args, thrown(error))
    throw error
  } finally {
    depth--
  }
}
function observeAsync (method, args, action, describe) {
  if (depth !== 0) return action()
  const line = callLine()
  depth++
  return Promise.resolve(action()).then(result => {
    try { if (recording()) record(method, args, describe === undefined ? null : describe(result), line); return result } finally { depth-- }
  }, error => {
    try { if (recording()) record(method, args, thrown(error), line); throw error } finally { depth-- }
  })
}

// —— 值描述：两侧（TS 探针与 Java 重放）必须给出同一表示 ——

function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function jsNumber (value) {
  return Number.isInteger(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER ? value : String(value)
}
function describeBytes (bytes) {
  if (bytes === null || bytes === undefined) return null
  return { kind: 'bytes', hex: hex(bytes) }
}
function describeNumbers (values) {
  if (values === null || values === undefined) return null
  return { kind: 'bytes', hex: hex(Uint8Array.from(values)) }
}
function describeScript (script) {
  if (script === null || script === undefined) return null
  return { asm: script.toASM(), hex: script.toHex() }
}
function describeTransaction (tx) {
  if (tx === null || tx === undefined) return null
  return { kind: 'transaction', inputs: tx.inputs === undefined ? 0 : tx.inputs.length,
    outputs: tx.outputs === undefined ? 0 : tx.outputs.length }
}
function describeInput (item) {
  return { sourceTXID: item.sourceTXID ?? null,
    sourceOutputIndex: jsNumber(item.sourceOutputIndex ?? 0),
    unlockingScript: describeScript(item.unlockingScript ?? null),
    sequence: item.sequence === undefined || item.sequence === null ? null : jsNumber(item.sequence),
    hasTemplate: item.unlockingScriptTemplate !== undefined && item.unlockingScriptTemplate !== null,
    hasSourceTransaction: item.sourceTransaction !== undefined && item.sourceTransaction !== null }
}
function describeOutput (item) {
  return { satoshis: item.satoshis === undefined || item.satoshis === null ? null : jsNumber(item.satoshis),
    lockingScript: describeScript(item.lockingScript ?? null),
    change: item.change === true }
}
function describeInputArgs (inputs) { return (inputs ?? []).map(describeInput) }
function describeOutputArgs (outputs) { return (outputs ?? []).map(describeOutput) }
function feeModel (model) {
  if (typeof model === 'number') return { kind: 'fixed', satoshis: jsNumber(model) }
  if (model.constructor && model.constructor.name === 'SatoshisPerKilobyte') {
    return { kind: 'satoshisPerKilobyte', value: jsNumber(model.value) }
  }
  return { kind: 'custom' }
}
// fee() 省略模型等于原地默认模型（固定原测试把 LivePolicy 换成 100 sat/kb）。
function describeFeeModel (model) {
  return model === undefined || model === null ? { kind: 'default', satoshisPerKilobyte: 100 } : feeModel(model)
}
// verify() 省略模型表示不使用费用模型，与 fee() 的默认模型不是同一件事。
function describeVerifyFeeModel (model) {
  return model === undefined || model === null ? null : feeModel(model)
}
function describeTracker (tracker) {
  if (tracker === undefined || tracker === null) return 'defaultTracker'
  if (typeof tracker === 'string') return tracker
  return 'tracker'
}
function describeSignOptions (options) {
  if (options === undefined || options === null) return null
  return { skipExistingSignatures: options.skipExistingSignatures === true }
}
function describeBroadcaster (broadcaster) {
  return broadcaster === undefined || broadcaster === null ? { kind: 'default' } : { kind: 'broadcaster' }
}
function describeBroadcastResult (result) {
  if (result === null || result === undefined) return null
  return { kind: 'broadcast', status: result.status ?? null, txid: result.txid ?? null, message: result.message ?? null }
}
function describeOptions (options) {
  if (options === undefined || options === null) return null
  return { kind: 'options',
    noSend: options.noSend === undefined ? null : options.noSend,
    acceptDelayedBroadcast: options.acceptDelayedBroadcast === undefined ? null : options.acceptDelayedBroadcast,
    returnTXIDOnly: options.returnTXIDOnly === undefined ? null : options.returnTXIDOnly,
    trustSelf: options.trustSelf === undefined ? null : options.trustSelf,
    randomizeOutputs: options.randomizeOutputs === undefined ? null : options.randomizeOutputs }
}
function describeOptional (value) { return value === undefined ? null : value }

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  depth = 0
})

function install (Original) {
  const originals = {}
  for (const name of ['fromHex', 'fromBinary', 'fromHexBEEF', 'fromBEEF', 'fromAtomicBEEF',
    'parseScriptOffsets']) originals[name] = Original[name]
  for (const name of ['addInput', 'addOutput', 'addP2PKHOutput', 'updateMetadata', 'fee', 'getFee', 'sign',
    'broadcast', 'toBinary', 'toEF', 'toHex', 'toHexBEEF', 'hash', 'id', 'verify', 'toBEEF', 'toAtomicBEEF',
    'toHexAtomicBEEF', 'completeWithWallet', 'preimage']) originals[name] = Original.prototype[name]

  Original.prototype.addInput = function (...args) {
    return observe('addInput', [describeInput(args[0])],
      () => Reflect.apply(originals.addInput, this, args))
  }
  Original.prototype.addOutput = function (...args) {
    return observe('addOutput', [describeOutput(args[0])],
      () => Reflect.apply(originals.addOutput, this, args))
  }
  Original.prototype.addP2PKHOutput = function (...args) {
    const target = typeof args[0] === 'string' ? { kind: 'string', value: args[0] } : describeNumbers(args[0])
    return observe('addP2PKHOutput', [target, args[1] === undefined ? null : jsNumber(args[1])],
      () => Reflect.apply(originals.addP2PKHOutput, this, args))
  }
  Original.prototype.updateMetadata = function (...args) {
    const metadata = args[0] ?? {}
    return observe('updateMetadata', [{ kind: 'metadata', labels: metadata.labels ?? null }],
      () => Reflect.apply(originals.updateMetadata, this, args))
  }
  Original.prototype.toHex = function (...args) {
    return observe('toHex', [], () => Reflect.apply(originals.toHex, this, args),
      result => ({ kind: 'string', value: result }))
  }
  Original.prototype.toHexBEEF = function (...args) {
    return observe('toHexBEEF', [], () => Reflect.apply(originals.toHexBEEF, this, args),
      result => ({ kind: 'string', value: result }))
  }
  Original.prototype.toHexAtomicBEEF = function (...args) {
    return observe('toHexAtomicBEEF', [], () => Reflect.apply(originals.toHexAtomicBEEF, this, args),
      result => ({ kind: 'string', value: result }))
  }
  Original.prototype.toBinary = function (...args) {
    return observe('toBinary', [], () => Reflect.apply(originals.toBinary, this, args), describeNumbers)
  }
  Original.prototype.toEF = function (...args) {
    return observe('toEF', [], () => Reflect.apply(originals.toEF, this, args), describeNumbers)
  }
  Original.prototype.toBEEF = function (...args) {
    return observe('toBEEF', [], () => Reflect.apply(originals.toBEEF, this, args), describeNumbers)
  }
  Original.prototype.toAtomicBEEF = function (...args) {
    return observe('toAtomicBEEF', [], () => Reflect.apply(originals.toAtomicBEEF, this, args), describeNumbers)
  }
  Original.prototype.hash = function (...args) {
    return observe('hash', [describeOptional(args[0])], () => Reflect.apply(originals.hash, this, args),
      result => (typeof result === 'string' ? { kind: 'string', value: result } : describeNumbers(result)))
  }
  Original.prototype.id = function (...args) {
    return observe('id', [describeOptional(args[0])], () => Reflect.apply(originals.id, this, args),
      result => (typeof result === 'string' ? { kind: 'string', value: result } : describeNumbers(result)))
  }
  Original.prototype.fee = function (...args) {
    const model = describeFeeModel(args[0])
    return observeAsync('fee', [model, describeOptional(args[1])],
      () => Reflect.apply(originals.fee, this, args))
  }
  Original.prototype.getFee = function (...args) {
    return observe('getFee', [], () => Reflect.apply(originals.getFee, this, args),
      result => ({ kind: 'number', value: String(result) }))
  }
  Original.prototype.sign = function (...args) {
    return observeAsync('sign', [describeSignOptions(args[0])],
      () => Reflect.apply(originals.sign, this, args))
  }
  Original.prototype.broadcast = function (...args) {
    return observeAsync('broadcast', [describeBroadcaster(args[0])],
      () => Reflect.apply(originals.broadcast, this, args), describeBroadcastResult)
  }
  Original.prototype.verify = function (...args) {
    return observeAsync('verify', [describeTracker(args[0]), describeVerifyFeeModel(args[1]),
      args[2] === undefined ? null : jsNumber(args[2])],
    () => Reflect.apply(originals.verify, this, args), result => result === true)
  }
  Original.prototype.completeWithWallet = function (...args) {
    return observeAsync('completeWithWallet',
      [{ kind: 'wallet' }, describeOptional(args[1]), describeOptional(args[2]), describeOptions(args[3])],
      () => Reflect.apply(originals.completeWithWallet, this, args))
  }
  Original.prototype.preimage = function (...args) {
    return observe('preimage', [describeOptional(args[0]), describeOptional(args[1]),
      describeScript(args[2] ?? null)], () => Reflect.apply(originals.preimage, this, args), describeNumbers)
  }
  Original.fromHex = function (...args) {
    return observe('fromHex', [args[0]], () => Reflect.apply(originals.fromHex, this, args), describeTransaction)
  }
  Original.fromBinary = function (...args) {
    return observe('fromBinary', [describeBytes(args[0])],
      () => Reflect.apply(originals.fromBinary, this, args), describeTransaction)
  }
  Original.fromHexBEEF = function (...args) {
    return observe('fromHexBEEF', [args[0], describeOptional(args[1])],
      () => Reflect.apply(originals.fromHexBEEF, this, args), describeTransaction)
  }
  Original.fromBEEF = function (...args) {
    return observe('fromBEEF', [describeBytes(args[0]), describeOptional(args[1])],
      () => Reflect.apply(originals.fromBEEF, this, args), describeTransaction)
  }
  Original.fromAtomicBEEF = function (...args) {
    return observe('fromAtomicBEEF', [describeBytes(args[0])],
      () => Reflect.apply(originals.fromAtomicBEEF, this, args), describeTransaction)
  }
  Original.parseScriptOffsets = function (...args) {
    return observe('parseScriptOffsets', [describeBytes(args[0])],
      () => Reflect.apply(originals.parseScriptOffsets, this, args), result => ({ kind: 'scriptOffsets',
        inputs: (result.inputs ?? []).map(item => [jsNumber(item.offset), jsNumber(item.length)]),
        outputs: (result.outputs ?? []).map(item => [jsNumber(item.offset), jsNumber(item.length)]) }))
  }
}

// 只包装真实模块的构造入口：刻意不改模块工厂，安装一次，避免循环引用时拿到半初始化的模块。
jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  install(moduleObject.default)
  const proxy = new Proxy(moduleObject.default, {
    construct (target, args, newTarget) {
      const instance = Reflect.construct(target, args, newTarget)
      if (depth === 0 && recording() && calledFromTest()) {
        record('constructor', [describeOptional(args[0]) ?? 1, describeInputArgs(args[1]), describeOutputArgs(args[2]),
          describeOptional(args[3]) ?? 0], describeTransaction(instance))
      }
      return instance
    }
  })
  moduleObject.default = proxy
  return moduleObject
})

// 采集期固定随机密钥；不改变测试逻辑，只让随机来源可复现（等价于冻结随机语料）。
jest.doMock(privateKeyPath, () => {
  const moduleObject = jest.requireActual(privateKeyPath)
  if (keyInstalled || moduleObject.default === undefined) return moduleObject
  keyInstalled = true
  const Original = moduleObject.default
  Original.fromRandom = function () { return new Original(1) }
  return moduleObject
})
