// 固定 src/script/__tests/Spend.codeseparator.test.ts 的 1 个原用例：只包装 Spend 构造函数，记录实际构造参数。
'use strict'
const path = require('node:path')
const recorder = require('./spend-probe-lib.cjs').create({
  output: process.env.MIGRATION_SPEND_CODESEPARATOR_TS_OBSERVATIONS,
  label: 'Spend codeseparator',
  testPath: expect.getState().testPath
})

beforeEach(() => { recorder.begin() })

const modulePath = path.resolve(path.dirname(expect.getState().testPath), '../Spend.ts')
jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
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
