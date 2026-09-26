// 固定 Mnemonic 原测试：只在原测试直接调用的公开入口记录参数和调用前状态。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_MNEMONIC_TS_OBSERVATIONS
if (!output) throw new Error('缺少 MIGRATION_MNEMONIC_TS_OBSERVATIONS')
const testPath = expect.getState().testPath
const sdk = path.resolve(path.dirname(testPath), '../../..')
const sourceFile = path.relative(sdk, testPath).replaceAll(path.sep, '/')
const mnemonicPath = path.join(sdk, 'src/compat/Mnemonic.ts')
const randomPath = path.join(sdk, 'src/primitives/Random.ts')
const wordlistPath = path.join(sdk, 'src/compat/bip-39-wordlist-en.ts')
const occurrences = new Map()
let occurrence = 0
let sequence = 0
const frozen = process.env.MIGRATION_MNEMONIC_RANDOM
  ? JSON.parse(fs.readFileSync(process.env.MIGRATION_MNEMONIC_RANDOM, 'utf8')) : null
let randomIndex = 0
afterAll(() => {
  if (frozen && randomIndex !== frozen.length) throw new Error('冻结随机输入未全部消费')
})

beforeEach(() => {
  const test = expect.getState().currentTestName
  occurrence = (occurrences.get(test) || 0) + 1
  occurrences.set(test, occurrence)
  sequence = 0
})

function state (object) {
  return { mnemonic: object.mnemonic, seedHex: Buffer.from(object.seed).toString('hex'),
    wordlist: object.Wordlist?.value?.length === 2048 ? 'english-2048' : 'other' }
}

function value (item) {
  if (item === undefined) return { kind: 'Undefined' }
  if (item === null) return { kind: 'Null' }
  if (typeof item === 'string') return { kind: 'String', value: item }
  if (typeof item === 'number') return { kind: 'Number', value: String(item) }
  if (Array.isArray(item) || item instanceof Uint8Array) {
    return { kind: 'ByteArray', bytesHex: Buffer.from(item).toString('hex') }
  }
  throw new Error(`Mnemonic 原测试实参尚未表征：${item?.constructor?.name || typeof item}`)
}

function directSource () {
  const frames = new Error().stack.split('\n')
  const firstCaller = frames.slice(2).find(line => !line.includes('capture-mnemonic-inputs.cjs'))
  if (!firstCaller || !firstCaller.includes('Mnemonic.test.ts:')) return null
  const match = firstCaller.match(/Mnemonic\.test\.ts:(\d+):\d+/)
  return match ? { file: sourceFile, line: Number(match[1]) } : null
}

function observe (method, args, before, source) {
  const test = expect.getState().currentTestName
  if (!test || !source) return
  fs.appendFileSync(output, JSON.stringify({ test, occurrence, sequence: ++sequence,
    method, args, preState: before, source }) + '\n')
}

function wrap (object) {
  let proxy
  proxy = new Proxy(object, {
    get (target, property) {
      const method = Reflect.get(target, property, target)
      if (typeof method !== 'function' || property === 'constructor') return method
      return function (...args) {
        const source = directSource()
        observe(String(property), args.map(value), state(target), source)
        const result = Reflect.apply(method, proxy, args)
        return result === target ? proxy : result
      }
    }
  })
  return proxy
}

jest.doMock(randomPath, () => {
  const original = jest.requireActual(randomPath)
  return { ...original, default: function (length) {
    const entry = frozen?.[randomIndex++]
    if (frozen && (!entry || entry.test !== expect.getState().currentTestName ||
        entry.occurrence !== occurrence || entry.args[0].value !== String(length))) {
      throw new Error('冻结随机输入的原用例/次数/长度不匹配')
    }
    const bytes = entry ? Array.from(Buffer.from(entry.preState.generatedBytesHex, 'hex')) : original.default(length)
    if (bytes.length !== length) throw new Error('冻结随机输入字节数错误')
    const source = new Error().stack.match(/Mnemonic\.test\.ts:(\d+):\d+/)
    observe('Random', [value(length)], { generatedBytesHex: Buffer.from(bytes).toString('hex') },
      { file: sourceFile, line: source ? Number(source[1]) : 0 })
    return bytes
  }, __esModule: true }
})

jest.doMock(wordlistPath, () => {
  const original = jest.requireActual(wordlistPath)
  const wordList = new Proxy(original.wordList, {
    get (target, property) {
      const result = Reflect.get(target, property, target)
      const source = directSource()
      if (property === 'value' && source?.line === 18) observe('wordList.value', [],
        { valueLength: result.length, space: target.space }, source)
      return result
    }
  })
  return { ...original, wordList, __esModule: true }
})

jest.doMock(mnemonicPath, () => {
  const original = jest.requireActual(mnemonicPath)
  const Mnemonic = new Proxy(original.default, {
    construct (target, args, newTarget) {
      const source = directSource()
      observe('constructor', args.map(value), null, source)
      return wrap(Reflect.construct(target, args, newTarget))
    },
    get (target, property, receiver) {
      if (property === 'toString') return target.toString.bind(target)
      const method = Reflect.get(target, property, receiver)
      if (typeof method !== 'function' || property === 'prototype') return method
      return function (...args) {
        const source = directSource()
        observe('static.' + String(property), args.map(value), null, source)
        return Reflect.apply(method, receiver, args)
      }
    }
  })
  // 包装不得改变原类的真实字符串观察。
  if (String(Mnemonic) !== String(original.default)) throw new Error('Mnemonic 类字符串被代理改变')
  return { ...original, default: Mnemonic, __esModule: true }
})
