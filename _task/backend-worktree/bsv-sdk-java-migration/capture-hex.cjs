// 固定原文件：src/primitives/__tests/hex.test.ts
// 只观察原始 hex.test.ts 的实际调用；返回值、异常和 Jest 断言保持不变。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.MIGRATION_HEX_OBSERVATIONS
if (!output) throw new Error('缺少 MIGRATION_HEX_OBSERVATIONS')
const sdk = path.dirname(expect.getState().testPath).replace(/\/src\/primitives\/__tests$/, '')
const hex = require(path.join(sdk, 'src/primitives/hex.ts'))

function value(input) {
  if (input === undefined) return { type: 'undefined' }
  if (input === null) return { type: 'null' }
  if (typeof input === 'string') return { type: 'string', value: input }
  throw new Error('Hex 采集器遇到未支持的类型')
}

for (const method of ['assertValidHex', 'normalizeHex']) {
  const original = hex[method]
  jest.spyOn(hex, method).mockImplementation(function (...args) {
    const location = new Error().stack.match(/\/hex\.test\.ts:(\d+):\d+/)
    if (!location || args.length !== 1) throw new Error('Hex 原测试调用位置或参数数量不符')
    const observation = { test: expect.getState().currentTestName, line: Number(location[1]), method, input: value(args[0]) }
    try {
      const result = Reflect.apply(original, this, args)
      observation.outcome = { kind: 'return', value: value(result) }
      return result
    } catch (error) {
      observation.outcome = { kind: 'throw', name: error.name, message: error.message }
      throw error
    } finally {
      fs.appendFileSync(output, JSON.stringify(observation) + '\n')
    }
  })
}
