'use strict'

const assert = require('node:assert/strict')
const { createHash } = require('node:crypto')
const { execFileSync } = require('node:child_process')
const { readFileSync } = require('node:fs')
const path = require('node:path')

// 独立补充有效输入；不改变固定原测试、向量或其断言站点。
const config = JSON.parse(readFileSync(path.join(__dirname, 'workspace.json'), 'utf8'))
const sdk = path.resolve(__dirname, '../../..', config.upstream.path, config.upstream.packagePath)
const upstreamCommit = execFileSync('git', ['-C', sdk, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim()
assert.equal(upstreamCommit, config.upstream.commit)
assert.equal(execFileSync('git', ['-C', sdk, 'status', '--porcelain', '--untracked-files=all'],
  { encoding: 'utf8' }).trim(), '')
const sha256 = value => createHash('sha256').update(value).digest('hex')
const sourceSha256 = {}
for (const name of ['DRBG', 'Hash', 'utils']) {
  const source = `src/primitives/${name}.ts`
  const actual = readFileSync(path.join(sdk, source))
  const frozen = execFileSync('git', ['-C', sdk, 'show',
    `${config.upstream.commit}:${config.upstream.packagePath}/${source}`])
  assert.equal(sha256(actual), sha256(frozen), `固定 TS 源码摘要不同：${source}`)
  sourceSha256[source] = sha256(actual)
  const built = `dist/cjs/src/primitives/${name}.js`
  sourceSha256[built] = sha256(readFileSync(path.join(sdk, built)))
}
const DRBG = require(path.join(sdk, 'dist/cjs/src/primitives/DRBG.js')).default
const hex = values => Buffer.from(values).toString('hex')
const seeds = [
  { id: 'repeated-bytes', entropyHex: '11'.repeat(32), nonceHex: '22'.repeat(32) },
  { id: 'zero-and-maximum-bytes', entropyHex: '00'.repeat(32), nonceHex: 'ff'.repeat(32) },
  { id: 'ascending-and-descending-bytes',
    entropyHex: hex(Array.from({ length: 32 }, (_, i) => i)),
    nonceHex: hex(Array.from({ length: 32 }, (_, i) => 255 - i)) }
]
const lengths = [16, 32, 64, 0, 1]
const vectors = seeds.map(seed => {
  const entropy = Array.from(Buffer.from(seed.entropyHex, 'hex'))
  const nonce = Array.from(Buffer.from(seed.nonceHex, 'hex'))
  assert.equal(entropy.length, 32)
  assert.equal(nonce.length, 32)
  const fromHex = new DRBG(seed.entropyHex, seed.nonceHex)
  const fromArrays = new DRBG(entropy, nonce)
  const repeated = new DRBG(seed.entropyHex, seed.nonceHex)
  const outputs = lengths.map(length => fromHex.generate(length))
  assert.deepEqual(lengths.map(length => fromArrays.generate(length)), outputs)
  assert.deepEqual(lengths.map(length => repeated.generate(length)), outputs)
  outputs.forEach((output, i) => assert.equal(output.length, 2 * lengths[i]))
  return { ...seed, lengths, outputs }
})
process.stdout.write(JSON.stringify({ schemaVersion: 1,
  scope: 'independent-valid-input-regression-not-original-test-replay',
  upstreamCommit, sourceSha256, vectors }, null, 2) + '\n')
