// 采集器自身回归；使用固定工作区 Jest matcher，不计入 SDK 迁移用例。
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const { createRequire } = require('node:module')
const { test } = require('node:test')

const sdk = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk')
const fromGlobals = createRequire(require.resolve('@jest/globals', { paths: [sdk] }))
const fromJestExpect = createRequire(fromGlobals.resolve('@jest/expect'))
const { expect: nativeExpect } = fromJestExpect('expect')
const file = path.resolve(__dirname, process.argv[2] || 'capture-parity.cjs')
const source = fs.readFileSync(file, 'utf8')

function exercise(code) {
  const rows = []
  const hooks = []
  const context = {
    expect: nativeExpect,
    require: name => name === 'node:fs'
      ? { appendFileSync: (_output, row) => rows.push(JSON.parse(row)) } : require(name),
    process: { env: { MIGRATION_PARITY_TS_OBSERVATIONS: 'in-memory' } },
    beforeEach: hook => hooks.push(hook), Buffer
  }
  context.global = context
  vm.runInNewContext(code, context, { filename: file })
  nativeExpect.setState({ currentTestName: '记录器语义回归', testPath: '/synthetic/semantics.test.ts' })
  hooks.forEach(hook => hook())
  const values = [undefined, null, 'value']
  const matchers = ['toBeUndefined', 'toBeDefined', 'not.toBeDefined']
  const passes = [[true, false, true], [false, true, false], [false, true, false]]
  for (let i = 0; i < values.length; i++) {
    for (let j = 0; j < matchers.length; j++) {
      const invoke = () => {
        const received = context.expect(values[i])
        return matchers[j].startsWith('not.') ? received.not.toBeDefined() : received[matchers[j]]()
      }
      if (passes[i][j]) assert.doesNotThrow(invoke)
      else assert.throws(invoke)
    }
  }
  return rows
}

function verify(rows) {
  assert.equal(rows.length, 9)
  const actuals = [{ type: 'undefined' }, { type: 'null' }, { type: 'string', value: 'value' }]
  const passes = [true, false, true, false, true, false, false, true, false]
  rows.forEach((row, index) => {
    assert.deepEqual(row.actual, actuals[Math.floor(index / 3)])
    assert.equal(row.pass, passes[index])
  })
}

test('Jest 的 undefined/null 判断及通过、失败轨迹均保留原 actual', () => verify(exercise(source)))

for (const [name, before, after] of [
  ['null 冒充 undefined', "if (value === null) return { type: 'null' }", "if (value === null) return { type: 'undefined' }"],
  ['defined 布尔投影', "return { receiver: received, getActual: () => canonical(received, 0, matcher === 'toEqual') }",
    "return { receiver: received, getActual: () => matcher === 'toBeDefined' ? canonical(received !== undefined) : canonical(received, 0, matcher === 'toEqual') }"],
  ['断言失败覆盖 actual', 'append(getActual(), failure === null)', 'append(failure ? thrown(failure) : getActual(), failure === null)']
]) {
  test(`拒绝篡改：${name}`, () => {
    assert.ok(source.includes(before), `缺少篡改站点：${name}`)
    assert.throws(() => verify(exercise(source.replace(before, after))))
  })
}
