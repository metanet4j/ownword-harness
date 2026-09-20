// 固定上游的小输入观察，不充抵 SDK 测试或 Java 对照。
import fs from 'node:fs'
import { createHash } from 'node:crypto'
const root = '/home/haodev/ownword/reference/ts-stack/packages/sdk/'
const files = ['BigNumber', 'utils', 'ReaderUint8Array', 'WriterUint8Array', 'ReductionContext', 'MontgomoryMethod', 'Mersenne', 'K256']
const hashes = Object.fromEntries(files.map(name => {
  const file = `dist/esm/src/primitives/${name}.js`
  return [file, createHash('sha256').update(fs.readFileSync(root + file)).digest('hex')]
}))
if (process.argv.includes('--without-buffer')) globalThis.Buffer = undefined
const { default: BN } = await import(root + 'dist/esm/src/primitives/BigNumber.js')
const U = await import(root + 'dist/esm/src/primitives/utils.js')
const { ReaderUint8Array: R } = await import(root + 'dist/esm/src/primitives/ReaderUint8Array.js')
const { WriterUint8Array: W } = await import(root + 'dist/esm/src/primitives/WriterUint8Array.js')
const { default: Red } = await import(root + 'dist/esm/src/primitives/ReductionContext.js')
const { default: Mont } = await import(root + 'dist/esm/src/primitives/MontgomoryMethod.js')
const { default: K256 } = await import(root + 'dist/esm/src/primitives/K256.js')
const cases = []
function observe(id, input, run) {
  try { cases.push({ id, input, result: run() }) }
  catch (e) { cases.push({ id, input, error: { name: e.name, message: e.message } }) }
}
observe('writers-negative-u64', -1, () => ({ array: new U.Writer().writeUInt64LE(-1).toArray(), typed: new W().writeUInt64LE(-1).toArray() }))
observe('writers-reference-and-number', [1, 2], () => {
  const input = [1, 2], chunks = [input], a = new U.Writer(chunks), b = new W(chunks)
  input[0] = 257.5
  return { array: a.toArray(), typed: b.toArray(), retainedChunks: a.bufs === chunks, retainedInput: a.bufs[0] === input, arrayHex: a.toHex(), helperHex: U.toHex(a.toArray()) }
})
observe('writer-stale-length', [1], () => {
  const input = [1], w = new U.Writer([input]); input.push(2)
  let typedError; try { w.toUint8Array() } catch (e) { typedError = { name: e.name, message: e.message } }
  return { cachedLength: w.getLength(), array: w.toArray(), typedError }
})
observe('writer-view-growth-reset', { initialCapacity: 2, bytes: [1, 2] }, () => {
  const w = new W(undefined, 2).write([1, 2]), v = w.toUint8ArrayZeroCopy(), c = w.toUint8Array()
  v[0] = 9
  const beforeGrow = w.toArray(); w.write([3]); v[1] = 8
  const afterGrow = w.toArray(), current = w.toUint8ArrayZeroCopy(); w.reset(); w.write([7])
  return { copy: [...c], oldView: [...v], beforeGrow, afterGrow, viewAfterReset: [...current], afterReset: w.toArray() }
})
observe('reader-reverse-short', { bytes: [1], length: 3 }, () => ({ array: new U.Reader([1]).readReverse(3), typed: [...new R([1]).readReverse(3)] }))
observe('read-varint-2pow53', [255, 0, 0, 0, 0, 0, 0, 32, 0], () => new R([255, 0, 0, 0, 0, 0, 0, 32, 0]).readVarIntNum(false))
observe('varint-fraction', 1.5, () => ({ static: U.Writer.varIntNum(1.5), array: new U.Writer().writeVarIntNum(1.5).toArray(), typed: new W().writeVarIntNum(1.5).toArray() }))
observe('array-and-byte-conversion', [257.5, -1, NaN, -0], () => ({ array: U.toArray([257.5, -1, NaN, -0]), typed: [...U.toUint8Array([257.5, -1, NaN, -0])] }))
observe('array-holes-and-undefined', 'new Array(2); a[1]=undefined', () => {
  const a = new Array(2); a[1] = undefined; const b = U.toArray(a)
  return { fresh: a !== b, present: [0 in b, 1 in b], value: b, typed: [...U.toUint8Array(a)] }
})
observe('base64-padding-bits', ['Z', 'Zh', 'Zh==', 'Z==='], () => ['Z', 'Zh', 'Zh==', 'Z==='].map(s => {
  try { return { input: s, result: U.base64ToArray(s) } } catch (e) { return { input: s, error: { name: e.name, message: e.message } } }
}))
observe('minimally-encode-mutation', [1, 0, 128], () => { const a = [1, 0, 128]; const b = U.minimallyEncode(a); return { inputAfter: a, result: b, same: a === b } })
observe('utf8-bom-and-surrogates', ['\ud800', [239, 187, 191, 65]], () => ({ encoded: U.toArray('\ud800'), decoded: U.toUTF8([239, 187, 191, 65]), invalid: U.toUTF8([237, 160, 128]) }))
observe('bn-words-copy-and-set', '-67108865', () => {
  const n = new BN('-67108865').expand(4), words = n.words; words[0] = 7
  const unchanged = n.toString(); n.words = [0x4000001, 0]
  return { unchanged, value: n.toString(), words: n.words, length: n.length, negative: n.negative }
})
observe('bn-strip-before-error', { value: 256, expand: 4, requestedBytes: 1 }, () => {
  const n = new BN(256).expand(4); let error
  try { n.toArray('be', 1) } catch (e) { error = { name: e.name, message: e.message } }
  return { lengthAfter: n.length, error }
})
observe('bn-zero-serialization', 0, () => {
  const n = new BN(0); n.negative = 1; const r = n.divmod(new BN(7))
  return { negative: n.negative, hex: n.toHex(), json: n.toJSON(), array: n.toArray(), sm: n.toSm(), quotientAndRemainderShare: r.div === r.mod, comparisonReciprocal: 1 / n.cmpn(0) }
})
observe('bn-hex-partial-le', '1g', () => new BN('1g', 16, 'le').toString())
observe('bn-hex-partial-be', '1g', () => new BN('1g', 16, 'be').toString())
observe('bn-number-fraction', 1.5, () => new BN(1.5))
observe('bn-composite-invmp', { value: 3, modulus: 8 }, () => ({ fermat: new BN(3)._invmp(new BN(8)).toString(), inverse: new BN(3).invm(new BN(8)).toString() }))
observe('red-context-identity', { modulus: 17, otherModulus: 13, value: 3 }, () => {
  const modulus = new BN(17), red = new Red(modulus), other = new Red(new BN(13)), a = new BN(3).toRed(other)
  red.verify1(a); red.verify2(a, a)
  const copied = red.convertFrom(a)
  return { retainedModulus: red.m === modulus, acceptedOtherContext: true, copied: copied !== a, redCleared: copied.red === null }
})
observe('red-negative-exponent', { value: 3, exponent: -2, modulus: 17 }, () => new BN(3).toRed(new Red(new BN(17))).redPow(new BN(-2)).fromRed().toString())
observe('red-imod-mutates', { value: 18, modulus: 17 }, () => {
  const a = new BN(18), red = new Red(new BN(17)), r = red.imod(a)
  return { same: a === r, value: a.toString(), redSame: a.red === red }
})
observe('mont-zero-imul', { value: 3, multiply: 0, modulus: 17 }, () => {
  const red = new Mont(new BN(17)), a = new BN(3).toRed(red), b = new BN(0).toRed(red), before = a.toString()
  let error; try { a.redIMul(b) } catch (e) { error = { name: e.name, message: e.message } }
  return { before, after: a.toString(), length: a.length, error, allocatingMul: a.redMul(b).fromRed().toString() }
})
observe('red-deterministic-sqrt', { value: 10, modulus: 13 }, () => [Red, Mont].map(Method => new BN(10).toRed(new Method(new BN(13))).redSqrt().fromRed().toString()))
observe('k256-split-nominal', { value: 1, expandedWords: 12 }, () => {
  const input = new BN(1).expand(12), out = new BN(0), k = new K256(); k.split(input, out)
  return { input: input.toString(), inputLength: input.length, output: out.toString(), outputLength: out.length }
})
observe('k256-imulk-nominal', { value: 0, expandedWords: 4 }, () => {
  const n = new BN(0).expand(4), k = new K256(), result = k.imulK(n)
  return { same: result === n, value: n.toString(), length: n.length, words: n.words }
})
console.log(JSON.stringify({ upstreamCommit: 'f999e0c1aad9a7afd0cbadaaf23841d049af9d5a', node: process.version, bufferAvailable: globalThis.Buffer !== undefined, hashes, collection: 'source-observations-only', cases }, (_, v) => {
  if (v === undefined) return { $type: 'undefined' }
  if (typeof v === 'number' && (!Number.isFinite(v) || Object.is(v, -0))) return { $type: 'number', value: Object.is(v, -0) ? '-0' : String(v) }
  if (typeof v === 'bigint') return { $type: 'bigint', value: String(v) }
  return v
}, 2))
