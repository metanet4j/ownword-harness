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

function harness(code) {
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
  return { context, rows }
}

function exercise(code) {
  const { context, rows } = harness(code)
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


test('调用参数编码保留 null、undefined、嵌套数组与所有调用', () => {
  const fromExpect = createRequire(fromJestExpect.resolve('expect'))
  const { fn } = fromExpect('jest-mock')
  const { context, rows } = harness(source)
  const mock = fn()
  const argument = { field: 'value' }
  mock(argument, null, undefined, [{}, null, undefined])
  mock('second')
  context.expect(mock).toHaveBeenCalledWith(argument, null, undefined, [{}, null, undefined])
  const opaque = { type: 'string', value: '[object Object]' }
  const nil = { type: 'null' }
  const missing = { type: 'undefined' }
  const first = { type: 'array', value: [opaque, nil, missing,
    { type: 'array', value: [opaque, nil, missing] }] }
  assert.deepEqual(rows[0].actual, { type: 'array', value: [first,
    { type: 'array', value: [{ type: 'string', value: 'second' }] }] })
  assert.deepEqual(rows[0].expected, first)
  assert.equal(mock.mock.calls[0][0], argument)
  assert.deepEqual(argument, { field: 'value' })
  assert.equal(mock.mock.calls[0][1], null)
  assert.equal(mock.mock.calls[0][2], undefined)
})

test('固定 Jest expect.any(Object) 接受 null 并拒绝 undefined 与原始值', () => {
  for (const value of [null, {}, [], new Error('value')]) {
    assert.doesNotThrow(() => nativeExpect(value).toEqual(nativeExpect.any(Object)))
  }
  for (const value of [undefined, 'text', 1, true, () => {}]) {
    assert.throws(() => nativeExpect(value).toEqual(nativeExpect.any(Object)))
  }
})
