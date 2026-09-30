// 固定 PushDrop.test.ts 原输入：随机根私钥材料、钱包实际返回的公钥与 DER 签名、
// PushDrop 的 lock／decode／unlock.sign／estimateLength 结果与异常。
// 原测试在 beforeEach 用 PrivateKey.fromRandom()，故把实际私钥记进样本供 Java 侧重建。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_PUSH_DROP_TS_OBSERVATIONS
if (!output) throw new Error('缺少 PushDrop 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const privateKeyPath = path.join(sdk, 'src/primitives/PrivateKey.ts')
const pushDropPath = path.join(sdk, 'src/script/templates/PushDrop.ts')
const walletPath = path.join(sdk, 'src/auth/certificates/__tests/CompletedProtoWallet.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let keyInstalled = false
let pushDropInstalled = false
let walletInstalled = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/PushDrop\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('PushDrop 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function scriptDescriptor (script) { return { asm: script.toASM(), hex: script.toHex() } }
function protocolDescriptor (value) {
  return Array.isArray(value) ? [value[0], value[1]] : null
}
function keyDescriptor (key) {
  return { hex: key.toHex(), wif: key.toWif(), publicKey: hex(Uint8Array.from(key.toPublicKey().encode(true))) }
}
function publicKeyArgsDescriptor (args) {
  return { protocolID: protocolDescriptor(args.protocolID), keyID: args.keyID ?? null,
    counterparty: args.counterparty ?? null, forSelf: args.forSelf === true }
}
function signatureArgsDescriptor (args) {
  return { protocolID: protocolDescriptor(args.protocolID), keyID: args.keyID ?? null,
    counterparty: args.counterparty ?? null, dataHex: hex(Uint8Array.from(args.data ?? [])) }
}
function fieldsDescriptor (fields) {
  return fields.map(field => Array.from(field))
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(privateKeyPath, () => {
  const moduleObject = jest.requireActual(privateKeyPath)
  if (keyInstalled || moduleObject.default === undefined) return moduleObject
  keyInstalled = true
  const Original = moduleObject.default
  const fromRandomOriginal = Original.fromRandom
  Original.fromRandom = function (...args) {
    const key = Reflect.apply(fromRandomOriginal, this, args)
    if (/PushDrop\.test\.ts:\d+:\d+/.test(new Error().stack)) record('fromRandom', [], keyDescriptor(key))
    return key
  }
  return moduleObject
})

jest.doMock(walletPath, () => {
  const moduleObject = jest.requireActual(walletPath)
  if (walletInstalled || moduleObject.CompletedProtoWallet === undefined) return moduleObject
  walletInstalled = true
  const Original = moduleObject.CompletedProtoWallet
  class ObservingWallet extends Original {
    constructor (...args) {
      super(...args)
      const getPublicKeyOriginal = this.getPublicKey.bind(this)
      const createSignatureOriginal = this.createSignature.bind(this)
      this.getPublicKey = async (...callArgs) => {
        const descriptor = publicKeyArgsDescriptor(callArgs[0] ?? {})
        try {
          const result = await getPublicKeyOriginal(...callArgs)
          record('getPublicKey', [descriptor], { publicKey: result.publicKey })
          return result
        } catch (error) {
          record('getPublicKey', [descriptor], thrown(error))
          throw error
        }
      }
      this.createSignature = async (...callArgs) => {
        const descriptor = signatureArgsDescriptor(callArgs[0] ?? {})
        try {
          const result = await createSignatureOriginal(...callArgs)
          record('createSignature', [descriptor], { signature: hex(Uint8Array.from(result.signature)) })
          return result
        } catch (error) {
          record('createSignature', [descriptor], thrown(error))
          throw error
        }
      }
    }
  }
  return { ...moduleObject, CompletedProtoWallet: ObservingWallet }
})

function install (Original) {
  const lockOriginal = Original.prototype.lock
  const unlockOriginal = Original.prototype.unlock
  const decodeOriginal = Original.decode
  Original.prototype.lock = async function (...args) {
    const descriptor = { fields: Array.isArray(args[0]) ? args[0].length : null,
      protocolID: protocolDescriptor(args[1]), keyID: args[2] ?? null, counterparty: args[3] ?? null,
      forSelf: args[4] === true, includeSignature: args[5] !== false,
      lockPosition: args[6] ?? 'before' }
    try {
      const script = await Reflect.apply(lockOriginal, this, args)
      record('lock', [descriptor], scriptDescriptor(script))
      return script
    } catch (error) {
      record('lock', [descriptor], thrown(error))
      throw error
    }
  }
  Original.prototype.unlock = function (...args) {
    const template = Reflect.apply(unlockOriginal, this, args)
    const signOriginal = template.sign
    const estimateOriginal = template.estimateLength
    return {
      sign: async (tx, inputIndex) => {
        try {
          const script = await Reflect.apply(signOriginal, template, [tx, inputIndex])
          record('sign', [inputIndex], scriptDescriptor(script))
          return script
        } catch (error) {
          record('sign', [inputIndex], thrown(error))
          throw error
        }
      },
      estimateLength: async (...rest) => {
        const value = await Reflect.apply(estimateOriginal, template, rest)
        record('estimateLength', [], value)
        return value
      }
    }
  }
  Original.decode = function (...args) {
    const position = args.length > 1 ? args[1] : 'before'
    const decoded = Reflect.apply(decodeOriginal, this, args)
    record('decode', [position], { fields: fieldsDescriptor(decoded.fields),
      lockingPublicKey: decoded.lockingPublicKey.toString() })
    return decoded
  }
}

jest.doMock(pushDropPath, () => {
  const moduleObject = jest.requireActual(pushDropPath)
  if (pushDropInstalled || moduleObject.default === undefined) return moduleObject
  pushDropInstalled = true
  install(moduleObject.default)
  return moduleObject
})
