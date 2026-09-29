// 固定 MerklePath.bench.test.ts 原输入：extract 的基路径与目标 txid、extract 结果、逐次 computeRoot。
// 原测试的 fixture 用 Math.random() 生成，Java 侧无法复现，因此把路径字节与目标一起登记为样本。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_MERKLE_PATH_BENCH_TS_OBSERVATIONS
if (!output) throw new Error('缺少 MerklePath bench 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/transaction/MerklePath.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let depth = 0
let installed = false
const extractedPaths = new WeakSet()

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/MerklePath\.bench\.test\.ts:(\d+):\d+/)
  if (!match) throw new Error('MerklePath bench 入口缺少固定原测试调用位置')
  return Number(match[1])
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('MerklePath bench 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  const MerklePath = moduleObject.default
  const extractOriginal = MerklePath.prototype.extract
  const computeRootOriginal = MerklePath.prototype.computeRoot
  MerklePath.prototype.extract = function (...args) {
    // hooks（beforeAll 里构造 fixture）没有当前用例身份，不计入口。
    if (depth !== 0 || !current()) return Reflect.apply(extractOriginal, this, args)
    depth++
    try {
      const targets = Array.from(args[0])
      const pathHex = this.toHex()
      const result = Reflect.apply(extractOriginal, this, args)
      extractedPaths.add(result)
      record('extract', [{ pathHex, targets }], { kind: 'bytes', hex: result.toHex() })
      return result
    } finally {
      depth--
    }
  }
  MerklePath.prototype.computeRoot = function (...args) {
    if (depth !== 0 || !current()) return Reflect.apply(computeRootOriginal, this, args)
    depth++
    try {
      const result = Reflect.apply(computeRootOriginal, this, args)
      record('computeRoot', [args[0] ?? null, extractedPaths.has(this) ? 'extracted' : 'base'],
        { kind: 'string', value: result })
      return result
    } finally {
      depth--
    }
  }
  return { ...moduleObject, default: MerklePath, __esModule: true }
})
