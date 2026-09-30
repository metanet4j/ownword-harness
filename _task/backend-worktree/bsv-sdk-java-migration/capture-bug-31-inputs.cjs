// 固定 bug-31.test.ts：原测试只用固定曲线参数与字符串构造，没有随机源；
// 入口是可复现的构造与静态转换，逐值登记后由 Java 侧重放。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_BUG_31_TS_OBSERVATIONS
if (!output) throw new Error('缺少 bug-31 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = 'src/primitives/__tests/bug-31.test.ts'
const privateKeyPath = path.join(sdk, 'src/primitives/PrivateKey.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let installedPrivateKey = false
let privateKeyNamespace = null

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/bug-31\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
/** 只登记本探针负责的原测试文件；同一次 Jest 运行里的其他原文件不属于本账本。 */
function mine () {
  const observed = expect.getState().testPath
  return typeof observed === 'string' && observed.endsWith('/' + sourceFile)
}
/** 模块加载期的固定调用不属于任何原用例，不进入账本。 */
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test || !mine()) return false
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
  return true
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}

function scalar (value) { return { kind: 'string', value: String(value) } }
function bigNumber (value) { return { kind: 'bigNumber', value: String(value) } }
// 构造入参可能是字符串或 BigNumber；两种语言下字符串表示一致，逐值登记。
function constructorArgs (args) {
  const list = []
  for (let index = 0; index < args.length; index++) {
    const value = args[index]
    if (typeof value === 'boolean') list.push({ kind: 'boolean', value })
    else if (value !== undefined) list.push(scalar(value))
  }
  return list
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

// 原测试唯一的构造入口是 new PrivateKey(...)：其中一次按 'error' 抛错、一次按 'nocheck' 不校验。
// 用 Proxy 包装真实类，保留 instanceof 与静态方法，只登记构造入参与结果。
jest.doMock(privateKeyPath, () => {
  const moduleObject = jest.requireActual(privateKeyPath)
  if (privateKeyNamespace !== null) return privateKeyNamespace
  if (moduleObject.default === undefined) return moduleObject
  installedPrivateKey = true
  const Original = moduleObject.default
  const proxy = new Proxy(Original, {
    construct (target, args, newTarget) {
      try {
        const value = Reflect.construct(target, args, newTarget)
        if (mine()) record('constructor', constructorArgs(args), bigNumber(String(value)))
        return value
      } catch (error) {
        if (mine()) record('constructor', constructorArgs(args), thrown(error))
        throw error
      }
    }
  })
  privateKeyNamespace = { __esModule: true, default: proxy }
  return privateKeyNamespace
})
