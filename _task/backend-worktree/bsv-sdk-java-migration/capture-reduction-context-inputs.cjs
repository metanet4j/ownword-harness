// 固定 ReductionContext.test.ts 原输入：约减上下文／Montgomery 上下文／K256 引擎的构造实参与结果。
// 三个类都用构造代理包装，内部构造（如 k256 里的 new K256）不重复记录，与 Java 侧一致。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_REDUCTION_CONTEXT_TS_OBSERVATIONS
if (!output) throw new Error('缺少 ReductionContext 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePaths = {
  ReductionContext: path.join(sdk, 'src/primitives/ReductionContext.ts'),
  MontgomoryMethod: path.join(sdk, 'src/primitives/MontgomoryMethod.ts'),
  K256: path.join(sdk, 'src/primitives/K256.ts')
}
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
const installed = new Set()

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/ReductionContext\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('ReductionContext 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function jsNumber (value) {
  return Number.isInteger(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER ? value : String(value)
}
function describeModulus (modulus) {
  return modulus === 'k256' ? { kind: 'string', value: 'k256' } : { kind: 'bignumber', hex: modulus.toString(16) }
}
function describeContext (context) {
  return { kind: 'context', modulus: context.m.toString(16), hasPrime: context.prime !== null }
}
function describeMontgomery (method) {
  return { kind: 'montgomery', shift: jsNumber(method.shift), r: method.r.toString(16),
    r2: method.r2.toString(16), rinv: method.rinv.toString(16), minv: method.minv.toString(16) }
}
function describeK256 (prime) { return { kind: 'k256', modulus: prime.p.toString(16) } }

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function install (moduleObject, name) {
  const handlers = {
    ReductionContext: describeContext,
    MontgomoryMethod: describeMontgomery,
    K256: describeK256
  }
  const Original = moduleObject.default
  const Wrapped = new Proxy(Original, {
    construct (target, args, newTarget) {
      // 同一个用例里嵌套构造（Montgomery 的 super、k256 里的 K256）不重复记录。
      if (depth !== 0) return Reflect.construct(target, args, newTarget === Wrapped ? target : newTarget)
      depth++
      try {
        const instance = Reflect.construct(target, args, newTarget === Wrapped ? target : newTarget)
        record(name, args.length === 0 ? [] : [describeModulus(args[0])], handlers[name](instance))
        return instance
      } catch (error) {
        record(name, args.length === 0 ? [] : [describeModulus(args[0])], thrown(error))
        throw error
      } finally {
        depth--
      }
    }
  })
  return { ...moduleObject, __esModule: true, default: Wrapped }
}

for (const [name, modulePath] of Object.entries(modulePaths)) {
  jest.doMock(modulePath, () => {
    const moduleObject = jest.requireActual(modulePath)
    if (installed.has(name) || moduleObject.default === undefined) return moduleObject
    installed.add(name)
    return install(moduleObject, name)
  })
}
