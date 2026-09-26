// 固定 Reader/Writer 原测试：记录构造与公开方法入口的真实入参和调用前状态。
'use strict'
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.MIGRATION_BYTE_IO_TS_OBSERVATIONS
if (!output) throw new Error('缺少 MIGRATION_BYTE_IO_TS_OBSERVATIONS')

const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const modulePath = path.join(sdk, 'src/primitives/utils.ts')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const classes = new Set(['Reader', 'ReaderUint8Array', 'Writer', 'WriterUint8Array'])
const occurrences = new Map()
let occurrence = 0
let sequence = 0
let receiverIndex = 0

beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
  receiverIndex = 0
})

function location () {
  const caller = new Error().stack.split('\n')[4] || ''
  const escaped = sourceFile.split('/').at(-1).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const match = caller.match(new RegExp(`${escaped}:(\\d+):\\d+`))
  return match ? Number(match[1]) : null
}

function snapshot (value, depth = 0) {
  if (depth > 5) throw new Error('Reader/Writer 实参层级超过采集边界')
  if (value === undefined) return { kind: 'Undefined' }
  if (value === null) return { kind: 'Null' }
  if (typeof value === 'number') return { kind: 'Number', value: Object.is(value, -0) ? '-0' : String(value) }
  if (typeof value === 'string') return { kind: 'String', value }
  if (typeof value === 'boolean') return { kind: 'Boolean', value }
  if (value instanceof Uint8Array) return { kind: 'Uint8Array', bytesHex: Buffer.from(value).toString('hex') }
  if (Array.isArray(value)) {
    if (value.every(item => Number.isInteger(item) && item >= 0 && item <= 255)) {
      return { kind: 'ByteArray', bytesHex: Buffer.from(value).toString('hex') }
    }
    return { kind: 'Array', values: value.map(item => snapshot(item, depth + 1)) }
  }
  if (value?.constructor?.name === 'BigNumber' && typeof value.toHex === 'function') {
    return { kind: 'BigNumber', hex: value.toHex(), decimal: value.toString() }
  }
  throw new Error(`Reader/Writer 实参类型尚未表征：${value?.constructor?.name || typeof value}`)
}

function state (className, target) {
  if (className.startsWith('Reader')) {
    return { bytesHex: Buffer.from(target.bin).toString('hex'), pos: target.pos }
  }
  const bytes = className === 'Writer' ? target.toArray() : target.toUint8Array()
  return { bytesHex: Buffer.from(bytes).toString('hex'), length: target.getLength() }
}

function observe (className, receiverId, method, args, before) {
  const test = expect.getState().currentTestName
  if (!test) return
  const line = location()
  if (line === null) return // 类内部调用不属于固定原测试的 API 边界。
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    receiverId, className, method, args: args.map(arg => snapshot(arg)),
    preState: before, source: { file: sourceFile, line } }) + '\n')
}

function wrap (className, instance, receiverId) {
  let proxy
  proxy = new Proxy(instance, {
    get (target, property) {
      const value = Reflect.get(target, property, target)
      if (typeof property !== 'string' || typeof value !== 'function' || property === 'constructor') return value
      return function (...args) {
        observe(className, receiverId, property, args, state(className, target))
        const result = Reflect.apply(value, target, args)
        return result === target ? proxy : result
      }
    }
  })
  return proxy
}

function proxyClass (className, original) {
  return new Proxy(original, {
    construct (target, args, newTarget) {
      const receiverId = ++receiverIndex
      observe(className, receiverId, 'constructor', args, null)
      const instance = Reflect.construct(target, args, newTarget)
      return wrap(className, instance, receiverId)
    }
  })
}

// Uint8Array 两类由 utils 再导出，且会反向引用 utils 的 Reader/Writer。
// 分别代理定义模块，避免在 utils 的循环加载期间替换整个导出对象。
const primaryUint8 = sourceFile.match(/(Reader|Writer)Uint8Array\.test\.ts$/)?.[1]
if (primaryUint8) {
  const className = `${primaryUint8}Uint8Array`
  const directPath = path.join(sdk, `src/primitives/${className}.ts`)
  jest.doMock(directPath, () => {
    const original = jest.requireActual(directPath)
    return { ...original, [className]: proxyClass(className, original[className]), __esModule: true }
  })
  if (primaryUint8 === 'Writer') {
    let readerPatched = false
    beforeEach(() => {
      if (readerPatched) return
      const { Reader } = jest.requireActual(modulePath)
      const read = Reader.prototype.readVarIntBn
      Reader.prototype.readVarIntBn = function (...args) {
        const receiverId = ++receiverIndex
        observe('Reader', receiverId, 'readVarIntBn', args, state('Reader', this))
        return read.apply(this, args)
      }
      readerPatched = true
    })
  } else {
    let writerPatched = false
    beforeEach(() => {
      if (writerPatched) return
      const { Writer } = jest.requireActual(modulePath)
      const originalWrite = Writer.prototype.writeVarIntBn
      const originalToArray = Writer.prototype.toArray
      const receivers = new WeakMap()
      const writerState = writer => {
        const bytes = originalToArray.call(writer)
        return { bytesHex: Buffer.from(bytes).toString('hex'), length: bytes.length }
      }
      Writer.prototype.writeVarIntBn = function (...args) {
        let receiverId = receivers.get(this)
        if (!receiverId) {
          receiverId = ++receiverIndex
          receivers.set(this, receiverId)
          if (writerState(this).length !== 0) throw new Error('辅助 Writer 构造状态不为空')
          observe('Writer', receiverId, 'constructor', [], null)
        }
        observe('Writer', receiverId, 'writeVarIntBn', args, writerState(this))
        return originalWrite.apply(this, args)
      }
      Writer.prototype.toArray = function (...args) {
        const receiverId = receivers.get(this)
        if (receiverId) observe('Writer', receiverId, 'toArray', args, writerState(this))
        return originalToArray.apply(this, args)
      }
      writerPatched = true
    })
  }
} else {
  jest.doMock(modulePath, () => {
    const original = jest.requireActual(modulePath)
    const replacements = {}
    for (const className of classes) {
      if (typeof original[className] === 'function') {
        replacements[className] = proxyClass(className, original[className])
      }
    }
    return { ...original, ...replacements, __esModule: true }
  })
}
