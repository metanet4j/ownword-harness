// 固定 Spend.test.ts 中属于 SpendCoreTest 的 20 个原用例：Spend 构造入口、
// 固定随机熵（与 Java 侧已登记私钥逐字节相同），以及两笔 coinbase 用例的 `Transaction.verify`。
// 同文件另外 455 个有效向量用例属于别的局部，由 recorder.active 自动跳过。
'use strict'
const path = require('node:path')
const recorder = require('./spend-probe-lib.cjs').create({
  output: process.env.MIGRATION_SPEND_CORE_TS_OBSERVATIONS,
  label: 'Spend core',
  testPath: expect.getState().testPath
})

// 取自既有证据 .cache/evidence/script-spend-ts-random.jsonl（Spend.test.ts 的 4 次 fromRandom）。
const RANDOM = new Map([
  ['Spend Successfully validates an R-puzzle spend',
    'ba8409613158901859eea765880d003fc86f11fa31cbae0d5dad11675bcd8e7c'],
  ['Spend Successfully validates an R-puzzle spend (HASH256)',
    'c930dbd8ff55a454871520a86f91cd04167071b8204ab941a080a455d51a39f3'],
  ['Spend Fails to validate an R-puzzle spend with the wrong K value',
    'c9a6d599fef375634a58c0b2b3a6d75f9bfe2104bbff61ca1e8247c463b362aa'],
  ['Spend Fails to validate an R-puzzle spend with the wrong hash',
    'bac90db10cfeada54036e3d9c61de618aca870019cfc385b1bba68ccc014a726']
])

beforeEach(() => { recorder.begin() })

// Transaction.verify 内部会自建 Spend 校验输入；该内部构造不是本用例的冻结入口，
// 用计数器在 verify 期间抑制 Spend 构造记录，两侧样本集合才一致。
let verifyDepth = 0

const scriptDir = path.dirname(expect.getState().testPath)
const spendPath = path.resolve(scriptDir, '../Spend.ts')
jest.doMock(spendPath, () => {
  const moduleObject = jest.requireActual(spendPath)
  return { ...moduleObject, __esModule: true, default: new Proxy(moduleObject.default, {
    construct (target, args, newTarget) {
      if (recorder.active && verifyDepth === 0) {
        if (args.length !== 1) throw new Error('固定 Spend 构造参数数量变化')
        recorder.spend(args[0])
      }
      return Reflect.construct(target, args, newTarget)
    }
  }) }
})

const randomPath = path.resolve(scriptDir, '../../primitives/Random.ts')
jest.doMock(randomPath, () => {
  const moduleObject = jest.requireActual(randomPath)
  const wrapped = length => {
    const value = RANDOM.get(recorder.current())
    if (value === undefined) throw new Error('固定随机输入未登记：' + recorder.current())
    if (length !== 32) throw new Error('固定随机输入长度不是 32：' + recorder.current())
    return Array.from(Buffer.from(value, 'hex'))
  }
  return { ...moduleObject, __esModule: true, default: wrapped }
})

const transactionPath = path.resolve(scriptDir, '../../transaction/Transaction.ts')
jest.doMock(transactionPath, () => {
  const moduleObject = jest.requireActual(transactionPath)
  const original = moduleObject.default
  // Transaction 与 Beef／BeefTx 循环引用：首次（嵌套）工厂调用时默认导出尚未就绪。
  if (original === undefined || original.__spendCoreProbeInstalled === true) return moduleObject
  {
    const verify = original.prototype.verify
    original.prototype.verify = function (...args) {
      if (!recorder.active) return Reflect.apply(verify, this, args)
      const chain = args[0]
      const headers = chain !== null && typeof chain === 'object' && chain.mock !== undefined &&
        Array.isArray(chain.mock.blockheaders) ? chain.mock.blockheaders.length : null
      const described = [{ headers: recorder.jsNumber(headers) }]
      // 与固定 TS 用例一致：先记录链头数量，再按 promise 解析/拒绝记录结果或异常。
      verifyDepth++
      return Promise.resolve(Reflect.apply(verify, this, args)).then(
        value => { verifyDepth--; recorder.record('Transaction.verify', described, value === undefined ? null : value); return value },
        error => { verifyDepth--; recorder.record('Transaction.verify', described, recorder.thrown(error)); throw error })
    }
    Object.defineProperty(original, '__spendCoreProbeInstalled', { value: true })
  }
  return moduleObject
})
