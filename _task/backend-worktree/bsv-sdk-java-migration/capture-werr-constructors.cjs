// 固定 WERR.test.ts 的三个公开构造器：只观察真正传入的参数，不改原断言。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.MIGRATION_WERR_TS_INPUTS
if (!output) throw new Error('缺少 WERR 输入采集路径')
const sdk = path.resolve(path.dirname(expect.getState().testPath), '../../..')

function tagged(value) {
  if (value === undefined) return { type: 'undefined' }
  if (value === null) return { type: 'null' }
  if (typeof value === 'boolean') return { type: 'boolean', value }
  if (typeof value === 'string') return { type: 'string', value }
  if (typeof value === 'number') {
    const bits = Buffer.alloc(8)
    bits.writeDoubleBE(value)
    return { type: 'number', bits: bits.toString('hex') }
  }
  if (Array.isArray(value)) return { type: 'array', value: value.map(tagged) }
  if (typeof value === 'object' && Object.getPrototypeOf(value) === Object.prototype)
    return { type: 'object', entries: Object.entries(value).map(([key, item]) => ({ key, value: tagged(item) })) }
  throw new Error('固定 WERR 构造器出现未支持的参数类型')
}

for (const name of ['WERR_REVIEW_ACTIONS', 'WERR_INSUFFICIENT_FUNDS', 'WERR_INVALID_PARAMETER']) {
  const modulePath = path.join(sdk, 'src/wallet', name + '.ts')
  jest.doMock(modulePath, () => {
    const moduleObject = jest.requireActual(modulePath)
    const Original = moduleObject[name]
    const observed = new Proxy(Original, {
      construct(target, args) {
        const test = expect.getState().currentTestName
        const location = new Error().stack.match(/\/WERR\.test\.ts:(\d+):\d+/)
        if (!test || !location) throw new Error('固定 WERR 原测试调用位置缺失')
        fs.appendFileSync(output, JSON.stringify({ test, line: Number(location[1]), method: name,
          args: args.map(tagged) }) + '\n')
        return Reflect.construct(target, args)
      }
    })
    return { ...moduleObject, [name]: observed, default: observed }
  })
}
