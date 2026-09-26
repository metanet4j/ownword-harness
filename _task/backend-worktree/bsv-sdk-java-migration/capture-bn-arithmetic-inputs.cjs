// 固定 BigNumber 原测试的真实公开入口及断言引用；不导出实际返回值作为重放输入。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.MIGRATION_BN_ARITHMETIC_RAW
if (!output) throw new Error('缺少 BigNumber arithmetic 原输入输出路径')
const variant = process.env.MIGRATION_BN_VARIANT || 'arithmetic'
if (!['arithmetic', 'binary', 'serializers'].includes(variant)) throw new Error('未知 BigNumber 固定测试变体')
const file = `src/primitives/__tests/BigNumber.${variant === 'arithmetic' ? 'arithmatic' : variant}.test.ts`
const nativeExpect = global.expect
const sdk = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk')
const ts = require(require.resolve('typescript', { paths: [sdk] }))
const ast = ts.createSourceFile(file, fs.readFileSync(path.join(sdk, file), 'utf8'), ts.ScriptTarget.Latest, true)
const assertionSpans = []
function collect(node) {
  if (ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression)) {
    let call = node.expression.expression
    if (ts.isPropertyAccessExpression(call) && call.name.text === 'not') call = call.expression
    if (ts.isCallExpression(call) && ts.isIdentifier(call.expression) && call.expression.text === 'expect') {
      const start = ast.getLineAndCharacterOfPosition(call.getStart(ast))
      const end = ast.getLineAndCharacterOfPosition(node.getEnd())
      assertionSpans.push({ line: start.line + 1, column: start.character + 1, endLine: end.line + 1 })
    }
  }
  ts.forEachChild(node, collect)
}
collect(ast)
let Original, originalString, active = false, depth = 0, sequence = 0, last
let ids = new WeakMap(), nextId = 0
const origins = new WeakMap()

function source() {
  const match = new Error().stack.match(/BigNumber\.(?:arithmatic|binary|serializers)\.test\.ts:(\d+):(\d+)/)
  if (!match) throw new Error('BigNumber arithmetic 调用缺少固定源码位置')
  return { file, line: Number(match[1]), column: Number(match[2]) }
}
function typed(value) {
  if (value === undefined) return { type: 'undefined' }
  if (value === null) return { type: 'null' }
  if (value instanceof Original) {
    if (!ids.has(value)) ids.set(value, ++nextId)
    const result = { type: 'BigNumber', id: ids.get(value), hex: originalString.call(value, 16) }
    if (origins.has(value)) result.origin = origins.get(value)
    return result
  }
  if (Array.isArray(value)) return { type: 'bytes', hex: Buffer.from(value).toString('hex') }
  if (value instanceof RegExp) return { type: 'regexp', source: value.source, flags: value.flags }
  if (['number', 'boolean', 'string'].includes(typeof value)) return { type: typeof value, value }
  throw new Error('未支持的 BigNumber 算术输入类型')
}
function binding(value) {
  if (value instanceof Original) return { type: 'BigNumber', id: typed(value).id }
  if (Array.isArray(value)) return { type: 'array', length: value.length }
  if (value && typeof value === 'object') {
    return { type: 'map', value: Object.fromEntries(Object.entries(value).map(([k, v]) => [k, binding(v)])) }
  }
  return { type: 'primitive' }
}
function emit(row) {
  fs.appendFileSync(output, JSON.stringify({ test: nativeExpect.getState().currentTestName,
    sequence: ++sequence, ...row }) + '\n')
}
function observe(method, receiver, args, action) {
  if (!active || depth) return action()
  // 通用断言记录器的 String/格式化调用不是原测试的公开入口。
  const caller = new Error().stack.split('\n').slice(2).find(line =>
    !line.includes('capture-bn-arithmetic-inputs.cjs') && !line.includes('/node_modules/jest-mock/'))
  if (!caller?.includes(path.basename(file) + ':')) return action()
  depth++
  const row = { kind: 'call', source: source(), method,
    receiver: receiver ? typed(receiver) : null, args: args.map(typed) }
  let result
  try {
    result = action()
    row.result = binding(result)
    return result
  } catch (error) {
    result = error
    row.result = { type: 'throw' }
    throw error
  } finally {
    depth--
    emit(row)
    last = { ref: sequence, value: result }
  }
}
beforeEach(() => { active = true; depth = 0; sequence = 0; last = null; ids = new WeakMap(); nextId = 0 })
afterEach(() => { active = false })
const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/primitives/BigNumber.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  Original = actual.default
  originalString = Original.prototype.toString
  for (const method of ['add', 'iadd', 'iaddn', 'addn', 'sub', 'isub', 'isubn', 'subn', 'mul',
    'imul', 'muln', 'imuln', 'pow', 'div', 'idivn', 'divRound', 'mod', 'umod', 'modrn',
    'abs', 'invm', 'gcd', 'egcd', 'ineg', 'neg', 'clone', 'sqr', 'isqr', 'ishln',
    'isNeg', 'cmp', 'cmpn', 'toNumber', 'toString', 'shln', 'ushln', 'shrn', 'ushrn',
    'bincn', 'imaskn', 'testn', 'bitLength', 'and', 'iand', 'or', 'ior', 'xor', 'ixor',
    'setn', 'notn', 'iushln', 'toJSON', 'toHex', 'toBits', 'toSm', 'toScriptNum', 'ltn']) {
    const original = Original.prototype[method]
    jest.spyOn(Original.prototype, method).mockImplementation(function (...args) {
      return observe(method, this, args, () => Reflect.apply(original, this, args))
    })
  }
  const negative = Object.getOwnPropertyDescriptor(Original.prototype, 'negative').get
  jest.spyOn(Original.prototype, 'negative', 'get').mockImplementation(function () {
    return observe('negative', this, [], () => negative.call(this))
  })
  for (const method of ['max', 'min', 'fromJSON', 'fromString', 'fromHex', 'fromNumber', 'fromBits', 'fromSm', 'fromScriptNum']) {
    const original = Original[method]
    jest.spyOn(Original, method).mockImplementation(function (...args) {
      return observe(method, null, args, () => Reflect.apply(original, Original, args))
    })
  }
  actual.default = new Proxy(Original, { construct(target, args) {
    const create = () => {
      const value = Reflect.construct(target, args)
      origins.set(value, args.map(typed))
      return value
    }
    return observe('constructor', null, args, create)
  } })
  return actual
})
// 此层位于通用 matcher 采集层之内，仅保存实际值来自哪个真实调用。
global.expect = Object.assign(function (actual) {
  const observed = source()
  const span = assertionSpans.find(item => item.line <= observed.line && item.endLine >= observed.line)
  if (!span) throw new Error('原断言没有固定 AST 范围')
  const location = { file, line: span.line, column: span.column }
  const actualEntry = last
  const assertion = nativeExpect(actual)
  function wrapMatcher(assertion, negated = false) {
    return new Proxy(assertion, { get(target, matcher) {
    if (matcher === 'not') return wrapMatcher(target.not, true)
    if (!['toBe', 'toEqual', 'toThrow'].includes(matcher)) throw new Error('未支持的 arithmetic matcher：' + String(matcher))
    return (...args) => {
      const expectedEntry = last !== actualEntry ? last : null
      const result = Reflect.apply(target[matcher], target, args)
      const received = matcher === 'toThrow' ? last : actualEntry
      if (!received) throw new Error('原断言没有实际 API 返回值引用')
      let transform = null
      if (matcher !== 'toThrow' && !Object.is(actual, received.value)) {
        if (typeof received.value === 'number' && received.value.toString(16) === actual) transform = 'number.toString(16)'
        else if (typeof received.value === 'boolean' && !received.value === actual) transform = 'boolean.not'
        else if (Array.isArray(received.value) && Buffer.from(received.value).toString('hex') === actual) transform = 'bytes.toHex'
        else throw new Error('原断言实际值不是已记录 API 返回值')
      }
      emit({ kind: 'assertion', source: location, matcher: (negated ? 'not.' : '') + matcher, actualRef: received.ref, transform,
        expected: expectedEntry ? { type: 'result', ref: expectedEntry.ref } : typed(args[0]) })
      return result
    }
  } })
  }
  return wrapMatcher(assertion)
}, nativeExpect)
