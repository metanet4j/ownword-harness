// 固定 SpendValildVectors.test.ts 里唯一的 Chronicle 向量（`Spend Valid Vectors 2 / 0 test`）：
// 只包装 Spend 构造函数，记录实际构造参数；原文件的其余 455 个向量由既有
// `capture-script-vector-inputs.cjs` 覆盖，本探针按冻结清单自动跳过。
'use strict'
const path = require('node:path')
const recorder = require('./spend-probe-lib.cjs').create({
  output: process.env.MIGRATION_SPEND_CHRONICLE_VECTOR_TS_OBSERVATIONS,
  label: 'Spend chronicle vector',
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
