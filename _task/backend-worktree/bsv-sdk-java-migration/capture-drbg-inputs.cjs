// 在固定 DRBG 原测试入口记录实际构造、生成参数、守卫分支操作数及结果。
// 原测试与 DRBG.vectors.ts 保持只读；分支样本只依据固定的 15 个 NIST 向量。
'use strict'
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.MIGRATION_DRBG_TS_OBSERVATIONS
if (!output) throw new Error('缺少 DRBG 输入输出路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const sourceName = path.basename(testPath)
const GUARD = sourceFile + ':15:9:conditional'
const OPERAND_LINES = { 10: 'entropy', 11: 'nonce' }
let sequence = 0
let occurrence = 0
let operands = []
let branchEmitted = false
const occurrences = new Map()
beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  operands = []
  branchEmitted = false
})
function encode (value) {
  if (value === undefined) return { type: 'undefined' }
  if (value === null) return { type: 'null' }
  if (typeof value === 'string' || typeof value === 'boolean' || typeof value === 'number') {
    return { type: typeof value, value }
  }
  if (Array.isArray(value)) return { type: 'array', value: value.map(encode) }
  throw new Error('未表征的 DRBG 输入类型：' + value?.constructor?.name)
}
function source () {
  const frame = new Error().stack.split('\n').slice(2).find(line =>
    line.includes(sourceName + ':') && !line.includes('capture-drbg-inputs.cjs'))
  if (!frame) return null
  const match = frame.match(/:(\d+):\d+\)?$/)
  return match ? { file: sourceFile, line: Number(match[1]) } : null
}
function write (value) {
  const test = expect.getState().currentTestName
  if (!test) return
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence, value }) + '\n')
}
function call (method, args, action) {
  const site = source()
  try {
    const result = action()
    if (site) {
      write({ kind: 'call', test: expect.getState().currentTestName, sequence: sequence + 1,
        source: site, method, args: args.map(encode) })
    }
    return result
  } catch (error) {
    if (site) {
      write({ kind: 'call', test: expect.getState().currentTestName, sequence: sequence + 1,
        source: site, method, args: args.map(encode) })
    }
    throw error
  }
}
function observeGuardOperand (value, encoding, bytes) {
  const site = source()
  const operand = site && OPERAND_LINES[site.line]
  if (!operand || encoding !== 'hex' || typeof value !== 'string' || !Array.isArray(bytes)) return
  operands.push({ operand, hex: value, length: bytes.length })
  if (branchEmitted || operands.length !== 2) return
  const entropy = operands.find(item => item.operand === 'entropy')
  const nonce = operands.find(item => item.operand === 'nonce')
  if (!entropy || !nonce) return
  if (entropy.length === 32 && nonce.length === 32) return
  branchEmitted = true
  write({ kind: 'branch', guardSiteId: GUARD, entropyHex: entropy.hex, nonceHex: nonce.hex,
    taken: true, controlFlow: 'return' })
}
const utilsPath = path.join(sdk, 'src/primitives/utils.ts')
jest.doMock(utilsPath, () => {
  const actual = jest.requireActual(utilsPath)
  const original = actual.toArray
  return { ...actual, toArray: function (value, encoding) {
    const bytes = Reflect.apply(original, this, [value, encoding])
    observeGuardOperand(value, encoding, bytes)
    return bytes
  } }
})
const filename = path.join(sdk, 'src/primitives/DRBG.ts')
jest.doMock(filename, () => {
  const actual = jest.requireActual(filename)
  const Real = actual.default
  const generate = Real.prototype.generate
  jest.spyOn(Real.prototype, 'generate').mockImplementation(function (...args) {
    return call('DRBG.generate', args, () => Reflect.apply(generate, this, args))
  })
  const wrapped = new Proxy(Real, {
    construct (target, args, newTarget) {
      return call('DRBG.constructor', args, () => Reflect.construct(target, args, newTarget))
    }
  })
  return { ...actual, default: wrapped, __esModule: true }
})
