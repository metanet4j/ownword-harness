// 固定 NormativeVectors.test.ts 的 9 个原用例：Spend 构造入口、sighash 用例的
// `TransactionSignature.format`／`formatOTDA`，以及 checksum 用例的 fixture 摘要。
'use strict'
const path = require('node:path')
const recorder = require('./spend-probe-lib.cjs').create({
  output: process.env.MIGRATION_NORMATIVE_VECTORS_TS_OBSERVATIONS,
  label: 'Normative vectors',
  testPath: expect.getState().testPath
})

const FIXTURE_ROOT = path.join(process.cwd(), 'src/script/__tests/fixtures')

beforeEach(() => { recorder.begin() })

const scriptDir = path.dirname(expect.getState().testPath)
const spendPath = path.resolve(scriptDir, '../Spend.ts')
jest.doMock(spendPath, () => {
  const moduleObject = jest.requireActual(spendPath)
  return { ...moduleObject, __esModule: true, default: new Proxy(moduleObject.default, {
    construct (target, args, newTarget) {
      if (recorder.active) {
        if (args.length !== 1) throw new Error('固定 Spend 构造参数数量变化')
        recorder.spend(args[0])
      }
      return Reflect.construct(target, args, newTarget)
    }
  }) }
})

const signaturePath = path.resolve(scriptDir, '../../primitives/TransactionSignature.ts')
jest.doMock(signaturePath, () => {
  const moduleObject = jest.requireActual(signaturePath)
  const original = moduleObject.default
  const describeBytes = values => ({ kind: 'bytes', hex: Buffer.from(values).toString('hex') })
  const wrapped = new Proxy(original, {
    get (target, property, receiver) {
      if (property === 'format' || property === 'formatOTDA') {
        return (...args) => recorder.observe('TransactionSignature.' + property,
          [recorder.describeSignatureParams(args[0])],
          () => Reflect.apply(target[property], target, args), describeBytes)
      }
      return Reflect.get(target, property, receiver)
    }
  })
  return { ...moduleObject, __esModule: true, default: wrapped }
})

// checksum 用例没有生产入口：把「固定 fixture 的 sha256 摘要」本身作为该用例的固定输入投影。
// 只在该用例激活时登记，且只对 fixtures 目录下的文件生效（其余 createHash 调用原样透传）。
let pendingFile = null
jest.doMock('node:fs', () => {
  const moduleObject = jest.requireActual('node:fs')
  const readFileSync = moduleObject.readFileSync
  return { ...moduleObject, readFileSync: (target, ...rest) => {
    const value = readFileSync(target, ...rest)
    if (recorder.active && typeof target === 'string' && target.startsWith(FIXTURE_ROOT)) {
      pendingFile = path.relative(FIXTURE_ROOT, target).replaceAll(path.sep, '/')
    }
    return value
  } }
})

jest.doMock('node:crypto', () => {
  const moduleObject = jest.requireActual('node:crypto')
  const createHash = moduleObject.createHash
  return { ...moduleObject, createHash: (algorithm, ...rest) => {
    const hash = createHash(algorithm, ...rest)
    if (!recorder.active || algorithm !== 'sha256') return hash
    const digest = hash.digest.bind(hash)
    hash.digest = (...args) => {
      const value = digest(...args)
      if (pendingFile !== null) {
        recorder.record('sha256File', [{ file: pendingFile }], value)
        pendingFile = null
      }
      return value
    }
    return hash
  } }
})
