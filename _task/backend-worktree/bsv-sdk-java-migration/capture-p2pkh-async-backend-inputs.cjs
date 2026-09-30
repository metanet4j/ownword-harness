// 固定 P2PKH.async-backend.test.ts 原输入：随机私钥材料、P2PKH lock／unlock.sign 结果，
// 以及注册的异步后端实际返回的 DER 签名与公钥。原测试用 PrivateKey.fromRandom()，
// 因此把实际使用的私钥记进样本，Java 侧据此重建同一把私钥与同一个后端桩。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_P2PKH_ASYNC_BACKEND_TS_OBSERVATIONS
if (!output) throw new Error('缺少 P2PKH async backend 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const privateKeyPath = path.join(sdk, 'src/primitives/PrivateKey.ts')
const p2pkhPath = path.join(sdk, 'src/script/templates/P2PKH.ts')
const asyncBackendPath = path.join(sdk, 'src/primitives/AsyncCryptoBackend.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let keyInstalled = false
let p2pkhInstalled = false
let backendInstalled = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/P2PKH\.async-backend\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('P2PKH async backend 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function hex (bytes) { return Buffer.from(bytes).toString('hex') }
function bytesDescriptor (bytes) { return { kind: 'bytes', hex: hex(bytes) } }
function scriptDescriptor (script) { return { asm: script.toASM(), hex: script.toHex() } }
function keyDescriptor (key) {
  return { hex: key.toHex(), wif: key.toWif(), publicKey: hex(Uint8Array.from(key.toPublicKey().encode(true))) }
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
    record('fromRandom', [], keyDescriptor(key))
    return key
  }
  return moduleObject
})

jest.doMock(p2pkhPath, () => {
  const moduleObject = jest.requireActual(p2pkhPath)
  if (p2pkhInstalled || moduleObject.default === undefined) return moduleObject
  p2pkhInstalled = true
  const Original = moduleObject.default
  const lockOriginal = Original.prototype.lock
  const unlockOriginal = Original.prototype.unlock
  Original.prototype.lock = function (...args) {
    const result = Reflect.apply(lockOriginal, this, args)
    record('lock', [typeof args[0] === 'string' ? args[0] : Array.from(args[0])], scriptDescriptor(result))
    return result
  }
  Original.prototype.unlock = function (...args) {
    const template = Reflect.apply(unlockOriginal, this, args)
    const signOriginal = template.sign
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
      estimateLength: template.estimateLength
    }
  }
  return moduleObject
})

jest.doMock(asyncBackendPath, () => {
  const moduleObject = jest.requireActual(asyncBackendPath)
  if (backendInstalled) return moduleObject
  backendInstalled = true
  const registerOriginal = moduleObject.registerAsyncCryptoBackend
  moduleObject.registerAsyncCryptoBackend = function (backend) {
    const signDigestOriginal = backend.signDigest
    const publicKeyOriginal = backend.publicKeyFromPrivate
    backend.signDigest = async (...args) => {
      try {
        const result = await Reflect.apply(signDigestOriginal, backend, args)
        record('signDigest', args.map(bytesDescriptor), bytesDescriptor(result))
        return result
      } catch (error) {
        record('signDigest', args.map(bytesDescriptor), thrown(error))
        throw error
      }
    }
    backend.publicKeyFromPrivate = async (...args) => {
      try {
        const result = await Reflect.apply(publicKeyOriginal, backend, args)
        record('publicKeyFromPrivate', args.map(bytesDescriptor), bytesDescriptor(result))
        return result
      } catch (error) {
        record('publicKeyFromPrivate', args.map(bytesDescriptor), thrown(error))
        throw error
      }
    }
    return Reflect.apply(registerOriginal, moduleObject, [backend])
  }
  return moduleObject
})
