// 固定 RPuzzle.test.ts 原输入：R 值、lock 锁定脚本、unlock 的 sign／estimateLength 实际结果。
// 原测试用固定 k=12345678 与固定私钥 PrivateKey(1)，两侧可逐值比较。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_R_PUZZLE_TS_OBSERVATIONS
if (!output) throw new Error('缺少 RPuzzle 原输入采集路径')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const modulePath = path.join(sdk, 'src/script/templates/RPuzzle.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let installed = false

function current () { return expect.getState().currentTestName }
function callLine () {
  const match = new Error().stack.match(/RPuzzle\.test\.ts:(\d+):\d+/)
  return match ? Number(match[1]) : null
}
function record (method, args, result, line = callLine()) {
  const test = current()
  if (!test) throw new Error('RPuzzle 入口发生在固定测试之外')
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    source: { file: sourceFile, line }, method, args, result }) + '\n')
}
function thrown (error) {
  const name = error && error.constructor ? error.constructor.name : String(error)
  return { kind: 'throw', name: name === 'SdkTypeException' ? 'TypeError' : name === 'SdkException' ? 'Error' : name,
    message: error && error.message !== undefined ? String(error.message) : null }
}
function scriptDescriptor (script) {
  return { asm: script.toASM(), hex: script.toHex() }
}

beforeEach(() => {
  const test = current()
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function install (Original) {
  const lockOriginal = Original.prototype.lock
  const unlockOriginal = Original.prototype.unlock
  Original.prototype.lock = function (...args) {
    const result = Reflect.apply(lockOriginal, this, args)
    record('lock', [Array.from(args[0])], scriptDescriptor(result))
    return result
  }
  Original.prototype.unlock = function (...args) {
    const template = Reflect.apply(unlockOriginal, this, args)
    const signOriginal = template.sign
    const estimateOriginal = template.estimateLength
    return {
      sign: async (tx, inputIndex) => {
        try {
          const script = await Reflect.apply(signOriginal, template, [tx, inputIndex])
          record('sign', [inputIndex], scriptDescriptor(script))
          return script
        } catch (error) {
          record('sign', [inputIndex], thrown(error))
          throw error
        }
      },
      estimateLength: async (...rest) => {
        const value = await Reflect.apply(estimateOriginal, template, rest)
        record('estimateLength', [], value)
        return value
      }
    }
  }
}

jest.doMock(modulePath, () => {
  const moduleObject = jest.requireActual(modulePath)
  if (installed || moduleObject.default === undefined) return moduleObject
  installed = true
  install(moduleObject.default)
  return moduleObject
})
