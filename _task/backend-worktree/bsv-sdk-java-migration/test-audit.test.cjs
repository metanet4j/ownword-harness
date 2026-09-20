// 只测试用户要求的命令行边界：清点用例与拒绝不完整的迁移证据。
const { test } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { spawnSync } = require('node:child_process')
const { createHash } = require('node:crypto')
const digest = bytes => createHash('sha256').update(bytes).digest('hex')

function evidenceFixture() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migration-audit-'))
  const write = (name, value) => fs.writeFileSync(path.join(dir, name), typeof value === 'string' ? value : JSON.stringify(value))
  write('catalog.json', { upstreamCommit: 'fixed', modules: ['compat'], moduleDependencies: { compat: [] }, files: [{ path: 'src/compat/a.test.ts', cases: [
    { id: 'case1', names: ['suite', 'one'], occurrence: 1, mode: 'run' },
    { id: 'case2', names: ['suite', 'two'], occurrence: 1, mode: 'run' }
  ], sites: [] }] })
  write('mapping.json', { upstreamCommit: 'fixed', siteReviews: [], cases: [
    { id: 'case1', java: [{ className: 'PortTest', name: 'one' }], assertionIds: ['a1'] },
    { id: 'case2', java: [{ className: 'PortTest', name: 'two' }], assertionIds: ['a2'] }
  ] })
  write('ts.json', { success: true, numTotalTests: 2, numPassedTests: 2, numFailedTests: 0, numPendingTests: 0, numTodoTests: 0, testResults: [{ name: '/sdk/src/compat/a.test.ts', status: 'passed', assertionResults: [
    { ancestorTitles: ['suite'], title: 'one', status: 'passed' },
    { ancestorTitles: ['suite'], title: 'two', status: 'passed' }
  ] }] })
  write('java.xml', '<testsuite tests="2" failures="0" errors="0" skipped="0"><testcase classname="PortTest" name="one"/><testcase classname="PortTest" name="two"/></testsuite>')
  write('observations.json', { upstreamCommit: 'fixed', javaRevision: 'test-revision',
    catalogSha256: digest(fs.readFileSync(path.join(dir, 'catalog.json'))),
    tsReportSha256: [digest(fs.readFileSync(path.join(dir, 'ts.json')))],
    javaReportSha256: [digest(fs.readFileSync(path.join(dir, 'java.xml')))],
    cases: ['case1', 'case2'].map((id, i) => ({ id, inputSha256: 'a'.repeat(64),
      tsInputSha256: 'a'.repeat(64), javaInputSha256: 'a'.repeat(64),
      ts: [{ id: 'a' + (i + 1), value: { type: 'hex', value: '0001' } }],
      java: [{ id: 'a' + (i + 1), value: { type: 'hex', value: '0001' } }] }))
  })
  return { dir, write, read: name => JSON.parse(fs.readFileSync(path.join(dir, name))),
    run: (extra = []) => spawnSync('python3', [path.join(__dirname, 'audit-tests.py'), 'compare', '--catalog', path.join(dir, 'catalog.json'), '--mapping', path.join(dir, 'mapping.json'), '--ts-report', path.join(dir, 'ts.json'), '--java-report', path.join(dir, 'java.xml'), '--observations', path.join(dir, 'observations.json'), ...extra], { encoding: 'utf8' }),
    close: () => fs.rmSync(dir, { recursive: true, force: true }) }
}

test('清点包含 each、循环、同名、skip、todo、only 和 manual；不执行测试体或 hooks', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migration-census-'))
  try {
    fs.writeFileSync(path.join(dir, 'jest.config.cjs'), "module.exports={testEnvironment:'node',testPathIgnorePatterns:['\\\\.man\\\\.test\\\\.js$']}\n")
    fs.mkdirSync(path.join(dir, 'src/primitives'), { recursive: true })
    fs.writeFileSync(path.join(dir, 'src/primitives/sample.man.test.js'), `
      beforeAll(() => { throw new Error('不应执行 hook') })
      afterAll(() => { throw new Error('不应执行 hook') })
      describe('全部用例', () => {
        test.each([1, 2])('参数 %s', () => { throw new Error('不应执行') })
        for (let i = 0; i < 2; i++) test('同名', () => { throw new Error('不应执行') })
        test.skip('跳过', () => {})
        test.todo('待办')
        test.only('聚焦', () => {})
        if (false) test('条件未注册', () => {})
      })
    `)
    const out = path.join(dir, 'census.json')
    const result = spawnSync(process.execPath, [path.join(__dirname, 'collect-cases.cjs'), '--sdk', dir, '--output', out, 'src/primitives/sample.man.test.js'], { encoding: 'utf8' })
    assert.equal(result.status, 0, result.stdout + result.stderr)
    const data = JSON.parse(fs.readFileSync(out))
    const cases = data.files[0].cases
    assert.equal(cases.length, 7)
    assert.equal(new Set(cases.map(c => c.id)).size, 7)
    assert.deepEqual(cases.map(c => c.names.at(-1)), ['参数 1', '参数 2', '同名', '同名', '跳过', '待办', '聚焦'])
    assert.deepEqual(cases.slice(-3).map(c => c.mode), ['skip', 'todo', 'only'])
    assert.ok(data.files[0].sites.some(s => s.kind === 'loop'))
    assert.ok(data.files[0].sites.some(s => s.kind === 'conditional'))
  } finally {
    fs.rmSync(dir, { recursive: true, force: true })
  }
})

test('清点依赖包含类型接口和跨模块测试辅助代码', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migration-dependencies-'))
  try {
    fs.mkdirSync(path.join(dir, 'src/script/__tests'), { recursive: true })
    fs.writeFileSync(path.join(dir, 'jest.config.cjs'), "module.exports={testEnvironment:'node'}\n")
    fs.writeFileSync(path.join(dir, 'src/script/sample.test.js'), "test('注册', () => {})\n")
    fs.writeFileSync(path.join(dir, 'src/script/Template.ts'), "import type { WalletInterface } from '../wallet/Wallet.interfaces.js'\nexport type Wallet = WalletInterface\n")
    fs.writeFileSync(path.join(dir, 'src/script/__tests/helper.ts'), "import { CompletedProtoWallet } from '../../auth/fixture.js'\nexport const wallet = CompletedProtoWallet\n")
    const out = path.join(dir, 'census.json')
    const result = spawnSync(process.execPath, [path.join(__dirname, 'collect-cases.cjs'), '--sdk', dir, '--output', out, 'src/script/sample.test.js'], { encoding: 'utf8' })
    assert.equal(result.status, 0, result.stdout + result.stderr)
    assert.deepEqual(JSON.parse(fs.readFileSync(out)).moduleDependencies.script, ['auth', 'wallet'])
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

const corruptions = [
  ['整模块依赖未纳入', f => { const d = f.read('catalog.json'); d.moduleDependencies.compat = ['primitives']; f.write('catalog.json', d) }, /依赖模块/],
  ['少一个映射', f => { const d = f.read('mapping.json'); d.cases.pop(); f.write('mapping.json', d) }, /未映射/],
  ['同一个 Java 测试冒充两个用例', f => { const d = f.read('mapping.json'); d.cases[1].java = d.cases[0].java; f.write('mapping.json', d) }, /重复/],
  ['总数相同但 TS 漏跑并重复另一用例', f => { const d = f.read('ts.json'); d.testResults[0].assertionResults[1].title = 'one'; f.write('ts.json', d) }, /实际用例/],
  ['Java 漏跑', f => f.write('java.xml', '<testsuite tests="1"><testcase classname="PortTest" name="one"/></testsuite>'), /未实际执行/],
  ['Java 跳过', f => f.write('java.xml', '<testsuite tests="2"><testcase classname="PortTest" name="one"><skipped/></testcase><testcase classname="PortTest" name="two"/></testsuite>'), /未通过/],
  ['TS 跳过', f => { const d = f.read('ts.json'); d.testResults[0].assertionResults[0].status = 'pending'; f.write('ts.json', d) }, /跳过/],
  ['缺少一个用例结果', f => { const d = f.read('observations.json'); d.cases.pop(); f.write('observations.json', d) }, /逐用例结果/],
  ['签名字节被篡改', f => { const d = f.read('observations.json'); d.cases[0].java[0].value.value = '0002'; f.write('observations.json', d) }, /结果不一致/],
  ['布尔值与数字不得混同', f => { const d = f.read('observations.json'); d.cases[0].ts[0].value = true; d.cases[0].java[0].value = 1; f.write('observations.json', d) }, /结果不一致/],
  ['异常语义不同', f => { const d = f.read('observations.json'); d.cases[0].ts[0].value = { error: 'Invalid checksum' }; d.cases[0].java[0].value = { error: 'Invalid key' }; f.write('observations.json', d) }, /结果不一致/],
  ['缺少一条断言结果', f => { const d = f.read('observations.json'); d.cases[0].java = []; f.write('observations.json', d) }, /断言结果/],
  ['重复结果行', f => { const d = f.read('observations.json'); d.cases.push(d.cases[0]); f.write('observations.json', d) }, /重复/],
  ['未复核源码循环或条件', f => { const d = f.read('catalog.json'); d.files[0].sites = [{ id: 'conditional:1', kind: 'conditional' }]; f.write('catalog.json', d) }, /复核/],
  ['映射来自另一上游版本', f => { const d = f.read('mapping.json'); d.upstreamCommit = 'other'; f.write('mapping.json', d) }, /版本/],
  ['原始 only 不得验收', f => { const d = f.read('catalog.json'); d.files[0].cases[0].mode = 'only'; f.write('catalog.json', d) }, /skip\/todo\/only/]
]
for (const [name, mutate, expected] of corruptions) test('拒绝：' + name, () => {
  const f = evidenceFixture()
  try {
    mutate(f)
    const observations = f.read('observations.json')
    observations.catalogSha256 = digest(fs.readFileSync(path.join(f.dir, 'catalog.json')))
    observations.tsReportSha256 = [digest(fs.readFileSync(path.join(f.dir, 'ts.json')))]
    observations.javaReportSha256 = [digest(fs.readFileSync(path.join(f.dir, 'java.xml')))]
    f.write('observations.json', observations)
    const result = f.run()
    assert.equal(result.status, 1, result.stdout + result.stderr)
    assert.match(result.stderr, expected)
  } finally { f.close() }
})

test('旧报告校验值和当前报告不同必须失败', () => {
  const f = evidenceFixture()
  try {
    fs.appendFileSync(path.join(f.dir, 'ts.json'), '\n')
    const result = f.run()
    assert.equal(result.status, 1)
    assert.match(result.stderr, /校验值/)
  } finally { f.close() }
})

test('完整的一比一映射、实际执行报告和逐断言结果通过证据核对', () => {
  const f = evidenceFixture()
  try { const result = f.run(); assert.equal(result.status, 0, result.stdout + result.stderr) }
  finally { f.close() }
})

test('报告汇总与实际用例矛盾时拒绝通过', () => {
  const f = evidenceFixture()
  try {
    const report = f.read('ts.json')
    report.numTotalTests = 3
    report.numPassedTests = 3
    f.write('ts.json', report)
    const observations = f.read('observations.json')
    observations.tsReportSha256 = [digest(fs.readFileSync(path.join(f.dir, 'ts.json')))]
    f.write('observations.json', observations)
    const result = f.run()
    assert.equal(result.status, 1, result.stdout + result.stderr)
    assert.match(result.stderr, /汇总/)
  } finally { f.close() }
})

test('TS 和 Java 输入不同即使输出相同也必须失败', () => {
  const f = evidenceFixture()
  try {
    const observations = f.read('observations.json')
    observations.cases[0].javaInputSha256 = 'b'.repeat(64)
    f.write('observations.json', observations)
    const result = f.run()
    assert.equal(result.status, 1, result.stdout + result.stderr)
    assert.match(result.stderr, /输入/)
  } finally { f.close() }
})

test('分阶段选择只接受完整模块名，模块内所有用例仍须映射', () => {
  const f = evidenceFixture()
  try {
    assert.equal(f.run(['--module', 'compat']).status, 0)
    assert.equal(f.run(['--module', 'compat/HD']).status, 1)
    const mapping = f.read('mapping.json')
    mapping.cases.pop()
    f.write('mapping.json', mapping)
    const result = f.run(['--module', 'compat'])
    assert.equal(result.status, 1)
    assert.match(result.stderr, /未映射/)
  } finally { f.close() }
})

test('旧 Java 源码版本的结果不能用于当前版本验收', () => {
  const f = evidenceFixture()
  try {
    const revision = spawnSync('python3', [path.join(__dirname, 'audit-tests.py'), 'revision'], { encoding: 'utf8' })
    assert.equal(revision.status, 0, revision.stderr)
    const current = JSON.parse(revision.stdout).javaRevision
    assert.match(current, /^[0-9a-f]{64}$/)
    const result = f.run(['--java-revision', current])
    assert.equal(result.status, 1)
    assert.match(result.stderr, /Java 源码版本/)
  } finally { f.close() }
})

test('TS 基线独立验收逐个核对冻结用例，不能用相同总数掩盖漏跑', () => {
  const f = evidenceFixture()
  try {
    const run = () => spawnSync('python3', [path.join(__dirname, 'audit-tests.py'), 'compare-ts', '--catalog', path.join(f.dir, 'catalog.json'), '--ts-report', path.join(f.dir, 'ts.json')], { encoding: 'utf8' })
    const valid = run()
    assert.equal(valid.status, 0, valid.stdout + valid.stderr)
    assert.equal(JSON.parse(valid.stdout).cases, 2)
    const report = f.read('ts.json')
    report.testResults[0].assertionResults[1].title = 'one'
    f.write('ts.json', report)
    const invalid = run()
    assert.equal(invalid.status, 1, invalid.stdout + invalid.stderr)
    assert.match(invalid.stderr, /实际用例/)
  } finally { f.close() }
})

test('离线基线拦截真实 fetch；即使调用方捕获异常也保留拒绝记录', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migration-offline-'))
  try {
    const log = path.join(dir, 'network.jsonl')
    const result = spawnSync(process.execPath, ['--require', path.join(__dirname, 'ts-offline-guard.cjs'), '-e', "fetch('https://example.invalid').catch(() => {})"], {
      encoding: 'utf8', env: { ...process.env, MIGRATION_NETWORK_LOG: log }
    })
    assert.equal(result.status, 0, result.stdout + result.stderr)
    const event = JSON.parse(fs.readFileSync(log, 'utf8').trim())
    assert.equal(event.transport, 'fetch')
    assert.equal(event.target, 'https://example.invalid')
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

test('离线基线拦截绕过 fetch 的原生 TCP 连接', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migration-offline-'))
  try {
    const log = path.join(dir, 'network.jsonl')
    const result = spawnSync(process.execPath, ['--require', path.join(__dirname, 'ts-offline-guard.cjs'), '-e', "try { require('node:net').connect({host:'127.0.0.1',port:1}) } catch {}"], {
      encoding: 'utf8', env: { ...process.env, MIGRATION_NETWORK_LOG: log }
    })
    assert.equal(result.status, 0, result.stdout + result.stderr)
    assert.equal(JSON.parse(fs.readFileSync(log, 'utf8').trim()).transport, 'socket')
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

test('上游钱包无服务场景使用明确失败 fixture，原断言保持不变', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migration-network-fixture-'))
  try {
    const log = path.join(dir, 'network.jsonl')
    const script = `
      global.expect = { getState: () => ({ testPath: '/sdk/src/wallet/__tests/WalletClient.additional.test.ts', currentTestName: 'WalletClient – signAction validation does NOT throw for a minimal valid signAction call structure (gets past validation)' }) }
      require(${JSON.stringify(path.join(__dirname, 'ts-offline-guard.cjs'))})
      fetch('http://localhost:3301/getVersion').catch(e => { if (e.cause?.code !== 'ECONNREFUSED') process.exitCode = 1 })
    `
    const result = spawnSync(process.execPath, ['-e', script], { encoding: 'utf8', env: { ...process.env, MIGRATION_NETWORK_LOG: log } })
    assert.equal(result.status, 0, result.stdout + result.stderr)
    assert.equal(fs.existsSync(log), false)
    const event = JSON.parse(fs.readFileSync(path.join(dir, 'network.fixtures.jsonl'), 'utf8').trim())
    assert.equal(event.fixture, 'wallet-unavailable')
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

test('默认链追踪器可调用性测试使用离线失败 fixture', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migration-chain-fixture-'))
  try {
    const log = path.join(dir, 'network.jsonl')
    const script = `
      global.expect = { getState: () => ({ testPath: '/sdk/src/transaction/chaintrackers/__tests/DefaultChainTracker.test.ts', currentTestName: 'defaultChainTracker WhatsOnChain defaults returns a tracker that responds to isValidRootForHeight as a function' }) }
      require(${JSON.stringify(path.join(__dirname, 'ts-offline-guard.cjs'))})
      fetch('https://api.whatsonchain.com/v1/bsv/main/block/0/header').catch(e => { if (e.cause?.code !== 'ECONNREFUSED') process.exitCode = 1 })
    `
    const result = spawnSync(process.execPath, ['-e', script], { encoding: 'utf8', env: { ...process.env, MIGRATION_NETWORK_LOG: log } })
    assert.equal(result.status, 0, result.stdout + result.stderr)
    assert.equal(fs.existsSync(log), false)
    assert.equal(JSON.parse(fs.readFileSync(path.join(dir, 'network.fixtures.jsonl'), 'utf8').trim()).fixture, 'chaintracker-unavailable')
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

test('连接参数含循环引用时仍先记录拒绝，不能因日志序列化而漏记', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migration-circular-connect-'))
  try {
    const log = path.join(dir, 'network.jsonl')
    const result = spawnSync(process.execPath, ['--require', path.join(__dirname, 'ts-offline-guard.cjs'), '-e', "const options={host:'127.0.0.1',port:1}; options.context=options; try { require('node:net').connect(options) } catch {}"], {
      encoding: 'utf8', env: { ...process.env, MIGRATION_NETWORK_LOG: log }
    })
    assert.equal(result.status, 0, result.stdout + result.stderr)
    assert.equal(JSON.parse(fs.readFileSync(log, 'utf8').trim()).transport, 'socket')
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

test('TS 清单与报告同时变成零用例也不能通过基线', () => {
  const f = evidenceFixture()
  try {
    const catalog = f.read('catalog.json')
    catalog.files[0].cases = []
    f.write('catalog.json', catalog)
    const report = f.read('ts.json')
    report.testResults[0].assertionResults = []
    report.numTotalTests = report.numPassedTests = 0
    f.write('ts.json', report)
    const result = spawnSync('python3', [path.join(__dirname, 'audit-tests.py'), 'compare-ts', '--catalog', path.join(f.dir, 'catalog.json'), '--ts-report', path.join(f.dir, 'ts.json')], { encoding: 'utf8' })
    assert.equal(result.status, 1, result.stdout + result.stderr)
    assert.match(result.stderr, /空用例/)
  } finally { f.close() }
})

test('API 清点覆盖深层导出、重载、属性、默认值、匿名类型和导出别名，不执行源码', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migration-api-'))
  try {
    fs.mkdirSync(path.join(dir, 'src/primitives/deep'), { recursive: true })
    fs.writeFileSync(path.join(dir, 'src/primitives/deep/Thing.ts'), `
      throw new Error('清点不得执行源码')
      export default class Thing {
        constructor(public value: number = 7) {}
        run(value: string): string
        run(value: number): number
        run(value: string | number): string | number { return value }
        get size(): number { return 1 }
        private secret = 2
      }
      export type Options = { count?: number; callback: (x: number) => Promise<string> }
      export const build = (options: Options = { callback: async () => 'ok' }): Thing => new Thing()
    `)
    fs.writeFileSync(path.join(dir, 'src/primitives/index.ts'), "export { default as Alias } from './deep/Thing.js'\n")
    const output = path.join(dir, 'api.json')
    const result = spawnSync(process.execPath, [path.join(__dirname, 'audit-api.cjs'), 'inventory', '--sdk', dir, '--module', 'primitives', '--output', output], { encoding: 'utf8' })
    assert.equal(result.status, 0, result.stdout + result.stderr)
    const data = JSON.parse(fs.readFileSync(output))
    assert.equal(data.files.length, 2)
    const entries = data.entries
    assert.ok(entries.some(e => e.name === 'Thing' && e.exportNames.includes('default')))
    assert.equal(entries.filter(e => e.name === 'Thing.run').length, 3)
    assert.ok(entries.some(e => e.name === 'Thing.value' && e.kind === 'parameter-property'))
    assert.ok(entries.some(e => e.name === 'Thing.secret' && e.visibility === 'private'))
    assert.ok(entries.some(e => e.name === 'Thing.size' && e.kind === 'get'))
    assert.ok(entries.some(e => e.name === 'Thing.constructor' && e.parameters[0].default === '7'))
    assert.ok(entries.some(e => e.name === 'Options' && e.signature.includes('callback: (x: number) => Promise<string>')))
    assert.ok(entries.some(e => e.name === 'build' && e.parameters[0].default.includes('callback')))
    assert.ok(data.exports.some(e => e.file === 'src/primitives/index.ts' && e.name === 'Alias' && e.targets.some(t => t.endsWith('#class:Thing:1'))))
    assert.equal(new Set(entries.map(e => e.id)).size, entries.length)
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

test('API 清点不能因测试目录名遗漏真实公开导出的辅助类', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migration-api-export-'))
  try {
    fs.mkdirSync(path.join(dir, 'src/auth/__tests'), { recursive: true })
    fs.writeFileSync(path.join(dir, 'src/auth/index.ts'), "export { Wallet } from './__tests/helper.js'\n")
    fs.writeFileSync(path.join(dir, 'src/auth/__tests/helper.ts'), 'export class Wallet { sign(data: number[]): number[] { return data } }\n')
    const output = path.join(dir, 'api.json')
    const result = spawnSync(process.execPath, [path.join(__dirname, 'audit-api.cjs'), 'inventory', '--sdk', dir, '--module', 'auth', '--output', output], { encoding: 'utf8' })
    assert.equal(result.status, 0, result.stdout + result.stderr)
    const data = JSON.parse(fs.readFileSync(output))
    assert.ok(data.entries.some(e => e.file === 'src/auth/__tests/helper.ts' && e.name === 'Wallet.sign'))
    assert.ok(data.exports.some(e => e.file === 'src/auth/index.ts' && e.name === 'Wallet'))
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

test('API 复核重新扫描源码；清单与映射同时漏掉接口也必须拒绝', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migration-api-check-'))
  try {
    fs.mkdirSync(path.join(dir, 'src/primitives'), { recursive: true })
    fs.writeFileSync(path.join(dir, 'src/primitives/a.ts'), 'export function one(): number { return 1 }\nexport function two(): number { return 2 }\n')
    const catalog = path.join(dir, 'api.json'), mapping = path.join(dir, 'map.json')
    const run = (command, extra) => spawnSync(process.execPath, [path.join(__dirname, 'audit-api.cjs'), command, '--sdk', dir, '--module', 'primitives', ...extra], { encoding: 'utf8' })
    const census = run('inventory', ['--output', catalog])
    assert.equal(census.status, 0, census.stdout + census.stderr)
    const full = JSON.parse(fs.readFileSync(catalog))
    const map = { entries: full.entries.map(e => ({ id: e.id, java: 'com.metanet4j.bsv.primitives.A#' + e.name, contract: 'API-NUMBER', review: 'pending' })) }
    fs.writeFileSync(mapping, JSON.stringify(map))
    let result = run('check', ['--catalog', catalog, '--mapping', mapping])
    assert.equal(result.status, 1, result.stdout + result.stderr)
    assert.match(result.stderr, /未复核/)
    map.entries.forEach(e => { e.review = 'reviewed' })
    fs.writeFileSync(mapping, JSON.stringify(map))
    result = run('check', ['--catalog', catalog, '--mapping', mapping])
    assert.equal(result.status, 0, result.stdout + result.stderr)
    map.upstreamCommit = 'wrong-version'
    fs.writeFileSync(mapping, JSON.stringify(map))
    result = run('check', ['--catalog', catalog, '--mapping', mapping])
    assert.equal(result.status, 1, result.stdout + result.stderr)
    assert.match(result.stderr, /上游版本/)
    delete map.upstreamCommit
    const missing = structuredClone(full)
    missing.entries.pop()
    map.entries.pop()
    fs.writeFileSync(catalog, JSON.stringify(missing))
    fs.writeFileSync(mapping, JSON.stringify(map))
    result = run('check', ['--catalog', catalog, '--mapping', mapping])
    assert.equal(result.status, 1, result.stdout + result.stderr)
    assert.match(result.stderr, /清单与固定源码不一致/)
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

test('API 清点保留根入口的别名和命名空间，只纳入选定模块的能力', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migration-api-root-'))
  try {
    fs.mkdirSync(path.join(dir, 'src/primitives'), { recursive: true })
    fs.mkdirSync(path.join(dir, 'src/excluded'), { recursive: true })
    fs.writeFileSync(path.join(dir, 'src/primitives/a.ts'), 'export function one(): number { return 1 }\n')
    fs.writeFileSync(path.join(dir, 'src/excluded/a.ts'), 'export const other = 2\n')
    fs.writeFileSync(path.join(dir, 'mod.ts'), "export { one as rootOne } from './src/primitives/a.js'\nexport * as Numbers from './src/primitives/a.js'\nexport * from './src/excluded/a.js'\n")
    const output = path.join(dir, 'api.json')
    const result = spawnSync(process.execPath, [path.join(__dirname, 'audit-api.cjs'), 'inventory', '--sdk', dir, '--module', 'primitives', '--output', output], { encoding: 'utf8' })
    assert.equal(result.status, 0, result.stdout + result.stderr)
    const data = JSON.parse(fs.readFileSync(output))
    assert.ok(data.exports.some(e => e.file === 'mod.ts' && e.name === 'rootOne'))
    assert.ok(data.exports.some(e => e.file === 'mod.ts' && e.name === 'Numbers' && e.targets.includes('namespace:src/primitives/a.ts')))
    assert.ok(!data.exports.some(e => e.name === 'other'))
    assert.ok(data.entryPoints.some(f => f.path === 'mod.ts' && f.sha256 === digest(fs.readFileSync(path.join(dir, 'mod.ts')))))
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

function apiBatchFixture() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migration-api-batches-'))
  fs.mkdirSync(path.join(dir, 'src/primitives'), { recursive: true })
  fs.writeFileSync(path.join(dir, 'src/primitives/one.ts'), 'export const one = 1\n')
  fs.writeFileSync(path.join(dir, 'src/primitives/two.ts'), 'export const two = 2\n')
  fs.writeFileSync(path.join(dir, 'src/primitives/index.ts'), "export * from './one.js'\nexport * from './two.js'\n")
  const catalog = path.join(dir, 'catalog.json'), mapping = path.join(dir, 'mapping.json'), features = path.join(dir, 'features.json')
  const run = (command, args = []) => spawnSync(process.execPath, [path.join(__dirname, 'audit-api.cjs'), command, '--sdk', dir, '--module', 'primitives', ...args], { encoding: 'utf8' })
  const census = run('inventory', ['--output', catalog])
  assert.equal(census.status, 0, census.stdout + census.stderr)
  const data = JSON.parse(fs.readFileSync(catalog))
  const map = { entries: data.entries.filter(e => e.name === 'one').map(e => ({ id: e.id, java: 'com.metanet4j.bsv.primitives.Values#one', contract: 'API-ONE', review: 'reviewed' })) }
  const state = { activeItem: 'two', nextItem: 'two', features: [
    { id: 'one', kind: 'api-batch', parentId: 'migration-api-contract', module: 'primitives', apiFiles: ['src/primitives/one.ts'], dependencies: [], status: 'done', evidence: ['API-ONE'] },
    { id: 'two', kind: 'api-batch', parentId: 'migration-api-contract', module: 'primitives', apiFiles: ['src/primitives/two.ts', 'src/primitives/index.ts'], dependencies: ['one'], status: 'in-progress', evidence: [] },
    { id: 'migration-api-contract', kind: 'gate', dependencies: ['one', 'two'], status: 'not-started' }
  ] }
  fs.writeFileSync(mapping, JSON.stringify(map)); fs.writeFileSync(features, JSON.stringify(state))
  return { catalog, data, map, state, save() { fs.writeFileSync(features, JSON.stringify(state)); fs.writeFileSync(mapping, JSON.stringify(map)) },
    run: (...args) => run('batches', ['--catalog', catalog, '--mapping', mapping, '--features', features, ...args]),
    close: () => fs.rmSync(dir, { recursive: true, force: true }) }
}

test('API 复核清单可嵌入编码任务，未完成全量设计不阻止已就绪任务执行', () => {
  const f = apiBatchFixture()
  try {
    f.state.apiBatches = f.state.features.splice(0, 2)
    f.state.apiBatches[1].status = 'not-started'
    f.state.features.push({ id: 'code', kind: 'implementation-slice', dependencies: [], status: 'in-progress' })
    for (const batch of f.state.apiBatches) batch.implementationTasks = ['code']
    f.state.activeItem = f.state.nextItem = 'code'
    f.save()
    let r = f.run()
    assert.equal(r.status, 0, r.stdout + r.stderr)
    assert.match(r.stdout, /未映射 1/)
    f.state.nextItem = 'two'; f.save()
    r = f.run()
    assert.equal(r.status, 1)
    assert.match(r.stderr, /nextItem.*编码任务|nextItem.*执行事项/)
    f.state.nextItem = 'code'
    f.state.apiBatches[0].implementationTasks = ['absent']; f.save()
    r = f.run()
    assert.equal(r.status, 1)
    assert.match(r.stderr, /API 复核.*编码任务/)
  } finally { f.close() }
})

test('编码任务必须完整分配 API 收口、原测试和辅助资料，缺失或重复均拒绝', () => {
  const f = apiBatchFixture()
  try {
    f.state.apiBatches = f.state.features.splice(0, 2)
    f.state.apiBatches[1].status = 'not-started'
    const testCatalog = path.join(path.dirname(f.catalog), 'tests.json')
    fs.writeFileSync(testCatalog, JSON.stringify({ files: [
      { path: 'src/primitives/one.test.ts', cases: [{ id: 'a' }] },
      { path: 'src/primitives/two.test.ts', cases: [{ id: 'b' }, { id: 'c' }] }
    ], moduleFiles: Object.fromEntries(['one.ts', 'two.ts', 'index.ts', 'one.test.ts', 'two.test.ts', 'vectors.json'].map(n => ['src/primitives/' + n, 'hash'])) }))
    f.state.implementationPolicy = { testCatalogRef: testCatalog }
    const coding = ['one', 'two'].map((name, i) => ({
      id: 'code-' + name, kind: 'implementation-slice', status: 'not-started', dependencies: [],
      sourceFiles: f.state.apiBatches[i].apiFiles.slice(), apiCompletionFiles: f.state.apiBatches[i].apiFiles.slice(),
      testFiles: ['src/primitives/' + name + '.test.ts'], regressionTestFiles: [],
      fixtureFiles: ['src/primitives/vectors.json'], apiBatchRefs: [name]
    }))
    f.state.features.push(...coding)
    for (const [i, batch] of f.state.apiBatches.entries()) batch.implementationTasks = [coding[i].id]
    f.state.activeItem = null; f.state.nextItem = coding[0].id
    f.save()
    let r = f.run()
    assert.equal(r.status, 0, r.stdout + r.stderr)
    assert.match(r.stdout, /编码任务.*2.*API 文件 3.*原测试文件 2.*原用例 3/)
    const original = structuredClone(f.state)
    for (const [change, message] of [
      [s => { s.features[2].testFiles = [] }, /原测试.*漏/],
      [s => { s.features[2].testFiles = s.features[1].testFiles.slice() }, /原测试.*重复/],
      [s => { s.features[2].apiCompletionFiles.pop() }, /API 收口.*漏/],
      [s => { s.features[2].apiCompletionFiles.push('src/primitives/one.ts') }, /API 收口.*重复|收口.*实现范围/],
      [s => { s.features[2].sourceFiles.push('src/primitives/unknown.ts') }, /实现范围.*未知/],
      [s => { s.features[2].apiBatchRefs = ['one'] }, /复核引用.*不符/],
      [s => { s.features[1].fixtureFiles = []; s.features[2].fixtureFiles = [] }, /辅助资料.*漏/],
      [s => { s.features[2].status = 'done'; s.features[2].evidence = ['假完成'] }, /编码任务.*API 未完成/]
    ]) {
      Object.assign(f.state, structuredClone(original)); change(f.state); f.save()
      r = f.run()
      assert.equal(r.status, 1, r.stdout + r.stderr)
      assert.match(r.stderr, message)
    }
  } finally { f.close() }
})

test('API 分批覆盖完整文件并保留全量未完成状态，单批可独立核对', () => {
  const f = apiBatchFixture()
  try {
    let r = f.run()
    assert.equal(r.status, 0, r.stdout + r.stderr)
    assert.match(r.stdout, /3 文件.*2 声明/)
    assert.match(r.stdout, /未映射 1/)
    r = f.run('--batch', 'one')
    assert.equal(r.status, 0, r.stdout + r.stderr)
    assert.match(r.stdout, /单批设计映射.*不是完整 API 或 SDK 验收/)
    r = f.run('--batch', 'two')
    assert.equal(r.status, 1, r.stdout + r.stderr)
    assert.match(r.stderr, /批次 two.*未映射 1/)
  } finally { f.close() }
})

test('API 未映射或未复核时，即使状态被改成 done 也拒绝通过', () => {
  const f = apiBatchFixture()
  try {
    f.state.features[1].status = 'done'
    f.state.features[1].evidence = ['伪造的完成记录']
    f.state.activeItem = null
    f.state.nextItem = 'migration-api-contract'
    f.save()
    let r = f.run()
    assert.equal(r.status, 1, r.stdout + r.stderr)
    assert.match(r.stderr, /未完成批次不能标记 done/)
    const two = f.data.entries.find(e => e.name === 'two')
    f.map.entries.push({ id: two.id, java: 'com.metanet4j.bsv.primitives.Values#two', contract: 'API-TWO', review: 'pending' })
    f.save()
    r = f.run()
    assert.equal(r.status, 1, r.stdout + r.stderr)
    assert.match(r.stderr, /未完成批次不能标记 done/)
  } finally { f.close() }
})

test('API 分批拒绝无效依赖、状态冒进和缺少证据的完成声明', () => {
  const f = apiBatchFixture()
  const original = structuredClone(f.state)
  try {
    for (const [change, message] of [
      [s => { s.features[0].evidence = [] }, /完成批次缺少证据/],
      [s => { s.features[0].status = 'not-started' }, /前置事项未完成/],
      [s => { s.features[1].dependencies = ['missing'] }, /未知依赖/],
      [s => { s.features[0].dependencies = ['two'] }, /依赖循环/],
      [s => { s.features[1].id = 'one' }, /功能项 ID 重复/],
      [s => { s.activeItem = 'one' }, /activeItem/],
      [s => { s.features[2].dependencies = ['one'] }, /总验收未依赖全部批次/],
      [s => { s.features[0].module = 'auth' }, /文件模块不符/],
      [s => { s.features[0].parentId = 'other' }, /API 批次父项/]
    ]) {
      Object.assign(f.state, structuredClone(original))
      change(f.state); f.save()
      const r = f.run()
      assert.equal(r.status, 1, r.stdout + r.stderr)
      assert.match(r.stderr, message)
    }
  } finally { f.close() }
})

test('API 分批不能遗漏零声明导出文件，也不能重复分配或随意增加文件', () => {
  const f = apiBatchFixture()
  const original = structuredClone(f.state)
  try {
    for (const [change, message] of [
      [s => { s.features[1].apiFiles.pop() }, /漏文件.*index.ts/],
      [s => { s.features[1].apiFiles.push('src/primitives/one.ts') }, /重复归属/],
      [s => { s.features[1].apiFiles.push('src/primitives/unknown.ts') }, /未知文件/]
    ]) {
      Object.assign(f.state, structuredClone(original))
      change(f.state); f.save()
      const r = f.run()
      assert.equal(r.status, 1, r.stdout + r.stderr)
      assert.match(r.stderr, message)
    }
    Object.assign(f.state, structuredClone(original))
    f.state.features[1].apiFiles.pop(); f.save()
    // 即使冻结清单与批次同时删除零声明文件，固定源码重新扫描仍必须识别。
    const missing = structuredClone(f.data)
    missing.files = missing.files.filter(e => e.path !== 'src/primitives/index.ts')
    missing.exports = missing.exports.filter(e => e.file !== 'src/primitives/index.ts')
    fs.writeFileSync(f.catalog, JSON.stringify(missing))
    const r = f.run()
    assert.equal(r.status, 1, r.stdout + r.stderr)
    assert.match(r.stderr, /清单与固定源码不一致/)
  } finally { f.close() }
})
