// 固定 Chronicle.test.ts 的 3 个原用例：Spend 构造入口，以及 wip 循环里逐行的
// `TransactionSignature.format`／`formatOTDA`（登记签名前置参数与实际前置字节）。
'use strict'
const path = require('node:path')
const recorder = require('./spend-probe-lib.cjs').create({
  output: process.env.MIGRATION_CHRONICLE_TS_OBSERVATIONS,
  label: 'Chronicle',
  testPath: expect.getState().testPath
})

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
