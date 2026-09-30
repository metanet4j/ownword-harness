// 固定上游行为观察；不改 TS，不计 SDK 原用例或 Java 对照通过数。
const fs = require('node:fs')
const vm = require('node:vm')
const path = require('node:path')
const crypto = require('node:crypto')
const assert = require('node:assert/strict')
const root = '/home/haodev/ownword/reference/ts-stack/packages/sdk'
const dir = path.join(root, 'dist/cjs/src/primitives')
const hashPath = path.join(dir, 'Hash.js')
const drbgPath = path.join(dir, 'DRBG.js')
const randomPath = path.join(dir, 'Random.js')
const originalGetBuiltin = process.getBuiltinModule
const originalBuffer = globalThis.Buffer
const cases = []
function result(run) {
  try { return { value: run() } } catch (e) {
    return { error: { name: e.name, message: e.message, code: e.code } }
  }
}
function observe(id, input, run) { cases.push({ id, input, ...result(run) }) }
const hex = a => originalBuffer.from(a).toString('hex')
const hashResults = []
try {
  for (const mode of ['native', 'fallback', 'fallback-without-buffer']) {
    process.getBuiltinModule = mode === 'native' ? originalGetBuiltin : () => { throw new Error('blocked for probe') }
    globalThis.Buffer = mode === 'fallback-without-buffer' ? undefined : originalBuffer
    delete require.cache[hashPath]
    delete require.cache[drbgPath]
    const H = require(hashPath)
    const DRBG = require(drbgPath).default
    assert.equal(new H.SHA256().native != null, mode === 'native')
    const record = (id, input, run) => observe(`${mode}/${id}`, input, run)
    const msg = Uint8Array.from([0, 1, 2, 3, 255, 254, 128])
    const values = Object.fromEntries(['sha1', 'sha256', 'sha512', 'ripemd160', 'hash160', 'hash256'].map(name => [name, hex(H[name](msg))]))
    for (const name of ['sha1', 'sha256', 'sha512', 'ripemd160']) {
      assert.equal(values[name], crypto.createHash(name).update(msg).digest('hex'))
    }
    assert.equal(values.hash256, crypto.createHash('sha256').update(crypto.createHash('sha256').update(msg).digest()).digest('hex'))
    assert.equal(values.hash160, crypto.createHash('ripemd160').update(crypto.createHash('sha256').update(msg).digest()).digest('hex'))
    hashResults.push(values)
    record('normal-digests', [...msg], () => values)
    record('toArray', '[257.5,-1,NaN,-0], sparse, float64, lone surrogate', () => {
      const a = [257.5, -1, NaN, -0], sparse = new Array(2); sparse[1] = undefined
      const b = H.toArray(a), c = H.toArray(sparse)
      return { array: b, fresh: a !== b, sparse: c, presence: [0 in c, 1 in c], typed: H.toArray(new Float64Array(a)), surrogate: H.toArray('\ud800'), oddHex: H.toArray('abc', 'hex'), falsy: H.toArray(null) }
    })
    record('ripemd-number-array', [256, -1, 3.5], () => ({ oneShot: hex(H.ripemd160([256, -1, 3.5])), class: new H.RIPEMD160().update([256, -1, 3.5]).digestHex() }))
    for (const name of ['SHA1', 'RIPEMD160', 'SHA256', 'SHA512', 'SHA1HMAC', 'SHA256HMAC', 'SHA512HMAC']) {
      record(`lifecycle-${name}`, { key: 'abc', msg: 'abc' }, () => {
        const h = new H[name]('abc'), updateReturnsSelf = h.update('abc') === h
        return { updateReturnsSelf, blockSize: h.blockSize, outSize: h.outSize, first: result(() => h.digestHex()), second: result(() => h.digest()), updateAfter: result(() => { h.update('x'); return 'accepted' }), pendingTotal: h.pendingTotal }
      })
    }
    for (const len of [-1, 1.5, NaN, Number.MAX_SAFE_INTEGER + 1]) {
      record('sha1-pad-invalid-' + String(len), len, () => { const h = new H.SHA1(); h.pendingTotal = len; return h._pad() })
    }
    for (const name of ['SHA1', 'RIPEMD160']) record(`pad-${name}`, 12345, () => { const h = new H[name](); h.pendingTotal = 12345; return h._pad().slice(-h.padLength) })
    record('pad-max-bits', { padLength: 1, pendingTotal: 40 }, () => { const h = new H.SHA1(); h.padLength = 1; h.pendingTotal = 40; return h._pad() })
    for (const [index, args] of [[1, undefined], [1, 0], [0, 32], [-1, 32], [1.5, 32], [1, null], [1, -1], [1, 1.5], [1, 65], [1, 32, 'sha256']].entries()) {
      record('pbkdf2-' + index, { password: [1, 2], salt: [3, 4], args }, () => H.pbkdf2([1, 2], [3, 4], ...args))
    }
    record('pbkdf2-string-input', { password: 'abc', salt: '12', iterations: 1, keylen: 8 }, () => H.pbkdf2('abc', '12', 1, 8))
    record('hmac-key-invalid', 'zz', () => new H.SHA256HMAC('zz'))
    record('drbg-validation-order', { entropy: [], nonce: 'zz' }, () => new DRBG([], 'zz'))
    const makeDrbg = () => new DRBG('11'.repeat(32), '22'.repeat(32))
    record('drbg-seed', ['undefined', 'empty', 'null'], () => [undefined, [], null].map(seed => {
      const d = makeDrbg(), oldK = d.K, oldV = d.V; d.update(seed)
      return { K: hex(d.K), V: hex(d.V), replacedK: d.K !== oldK, replacedV: d.V !== oldV }
    }))
    for (const len of [0, -1, 1.5, 33, NaN]) record('drbg-length-' + String(len), len, () => {
      const d = makeDrbg(), before = hex(d.K); const out = d.generate(len)
      return { out, advanced: before !== hex(d.K), K: hex(d.K), V: hex(d.V), next: d.generate(4) }
    })
    record('endian', [0x11223344, -1, 2 ** 32 + 1, NaN], () => [0x11223344, -1, 2 ** 32 + 1, NaN].map(n => ({ swap: H.swapBytes32(n), alias: H.htonl(n), real: H.realHtonl(n) })))
    if (mode !== 'native') record('fast-state-clone-destroy', 'abc', () => {
      const h = new H.SHA256().update('abc').h, c = h.clone()
      assert.equal(hex(c.digest()), crypto.createHash('sha256').update('abc').digest('hex'))
      const flagsAfterCloneDigest = { finished: c.finished, destroyed: c.destroyed }
      const manual = new H.SHA256().h; manual.destroy()
      return { flagsAfterCloneDigest, cloneBufferSeparate: c.buffer !== h.buffer, manualDestroyFlags: { finished: manual.finished, destroyed: manual.destroyed }, updateAfterManualDestroy: result(() => { manual.update(new Uint8Array([1])); return 'accepted' }), original: hex(h.digest()) }
    })
  }
  assert.deepEqual(hashResults[0], hashResults[1]); assert.deepEqual(hashResults[1], hashResults[2])
} finally {
  process.getBuiltinModule = originalGetBuiltin
  globalThis.Buffer = originalBuffer
  delete require.cache[hashPath]; delete require.cache[drbgPath]
}

// 用独立 VM 复现模块隔离和宿主能力；只填充可追踪字节，不使用固定假随机作生产实现。
const randomSource = fs.readFileSync(randomPath, 'utf8')
function loadRandom(env) {
  const context = vm.createContext({ ...env, exports: {} })
  vm.runInContext(randomSource, context, { filename: randomPath, timeout: 1000 })
  return { run: context.exports.default, context }
}
for (const branch of ['global', 'self', 'window', 'node', 'none']) {
  const calls = [], fill = n => ({ getRandomValues(a) { calls.push({ branch: n, len: a.length }); a.fill(n); return new Uint8Array([9]) } })
  const env = { crypto: fill(11), self: { crypto: fill(22) }, window: { crypto: fill(33) }, process: { getBuiltinModule(name) { calls.push({ builtin: name }); return { randomBytes(n) { calls.push({ branch: 44, len: n }); return Uint8Array.from({ length: n }, () => 44) } } } } }
  if (branch !== 'global') delete env.crypto
  if (!['global', 'self'].includes(branch)) delete env.self
  if (['node', 'none'].includes(branch)) delete env.window
  if (branch === 'none') delete env.process
  observe(`random/${branch}`, { len: 3, capabilities: Object.keys(env) }, () => { const r = loadRandom(env); return { first: result(() => r.run(3)), second: result(() => r.run(3)), calls } })
}
observe('random/global-dynamic', [1, 2], () => {
  const r = loadRandom({ crypto: { getRandomValues(a) { a.fill(1) } } })
  const first = r.run(2); r.context.crypto = { getRandomValues(a) { a.fill(2) } }
  return { first, second: r.run(2) }
})
observe('random/noRand-cached', 1, () => {
  const r = loadRandom({}); const first = result(() => r.run(1))
  r.context.crypto = { getRandomValues(a) { a.fill(1) } }
  return { first, afterCapabilityAdded: result(() => r.run(1)) }
})
observe('random/builtin-error-retry', 1, () => {
  let count = 0
  const r = loadRandom({ process: { getBuiltinModule() { count++; throw new Error('builtin failure') } } })
  return { first: result(() => r.run(1)), second: result(() => r.run(1)), count }
})
for (const mode of ['web', 'node']) for (const len of [0, -1, -0.5, 1.5, NaN, 65537]) {
  observe(`random/${mode}-length-${String(len)}`, len, () => {
    const env = mode === 'web' ? { crypto: crypto.webcrypto } : { process: { getBuiltinModule: () => crypto } }
    const out = loadRandom(env).run(len)
    return { length: out.length, allBytes: out.every(n => Number.isInteger(n) && n >= 0 && n <= 255) }
  })
}
const files = ['Hash', 'DRBG', 'Random', 'hex', 'utils'].flatMap(n => [`src/primitives/${n}.ts`, `dist/cjs/src/primitives/${n}.js`])
assert.equal(new Set(cases.map(c => c.id)).size, cases.length)
const hashes = Object.fromEntries(files.map(f => [f, crypto.createHash('sha256').update(fs.readFileSync(path.join(root, f))).digest('hex')]))
console.log(JSON.stringify({ upstreamCommit: 'f999e0c1aad9a7afd0cbadaaf23841d049af9d5a', node: process.version, collection: 'source-observations-only', hashes, cases }, (_, v) => {
  if (v === undefined) return { $type: 'undefined' }
  if (typeof v === 'number' && (!Number.isFinite(v) || Object.is(v, -0))) return { $type: 'number', value: Object.is(v, -0) ? '-0' : String(v) }
  return v
}, 2))
