import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {execFileSync, spawn} from 'node:child_process';

const taskDir = path.dirname(fileURLToPath(import.meta.url));
const workspace = path.resolve(taskDir, '../../..');
const mode = process.argv[2] ?? '--check';
assert.ok(['--check', '--serve'].includes(mode) && process.argv.length <= 3,
  '用法：node bootstrap.mjs [--check|--serve]');
const readJson = file => JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
const state = readJson(path.join(taskDir, 'feature_list.json'));
const env = state.environment;
const prototype = path.resolve(taskDir, env.worktree);
const run = (command, args, cwd = prototype) => execFileSync(command, args, {
  cwd, encoding: 'utf8', windowsHide: true, stdio: ['ignore', 'pipe', 'pipe']
}).trim();
const git = (...args) => run('git', ['-C', prototype, ...args]);

assert.ok(fs.statSync(path.join(prototype, '.git')).isFile(), '原型必须是 Git worktree');
assert.equal(git('branch', '--show-current'), env.branch, '分支与任务登记不一致');
git('merge-base', '--is-ancestor', env.baselineCommit, 'HEAD');
const sourceDir = path.resolve(workspace, env.sourceRepository);
assert.equal(fs.realpathSync(git('rev-parse', '--path-format=absolute', '--git-common-dir')),
  fs.realpathSync(run('git', ['-C', sourceDir, 'rev-parse', '--path-format=absolute', '--git-common-dir'])),
  'worktree 不属于登记的原型仓库');
const prdPath = path.resolve(workspace, env.prdSource);
const prd = fs.readFileSync(prdPath, 'utf8');
assert.ok(prd.includes(`# Ownword 产品设计 ${env.prdVersion}`), 'PRD 版本不一致');
assert.ok(fs.existsSync(path.resolve(workspace, state.designReview.source)), '缺少设计审查报告');

const bdd = [...prd.matchAll(/^\| (A\d{2}-[A-Z]|X\d{2}) \|/gm)].map(match => match[1]);
assert.equal(new Set(bdd).size, bdd.length, 'BDD 编号重复');
const byId = new Map(state.features.map(feature => [feature.id, feature]));
assert.equal(byId.size, state.features.length, '功能编号重复');
const covered = new Set();
for (const feature of state.features) {
  assert.ok(state.allowedStatuses.includes(feature.status), `非法状态：${feature.id}`);
  assert.ok(feature.doneCriteria?.length, `缺少完成条件：${feature.id}`);
  for (const dependency of feature.dependencies) assert.ok(byId.has(dependency), `缺少依赖：${dependency}`);
  for (const ref of feature.acceptanceRefs ?? []) {
    assert.ok(bdd.includes(ref), `不存在的验收引用：${ref}`);
    covered.add(ref);
  }
}
const visited = new Set();
function visit(id, chain = new Set()) {
  assert.ok(!chain.has(id), `功能依赖成环：${id}`);
  if (visited.has(id)) return;
  for (const dependency of byId.get(id).dependencies) visit(dependency, new Set([...chain, id]));
  visited.add(id);
}
for (const id of byId.keys()) visit(id);
assert.deepEqual([...covered].sort(), [...bdd].sort(), 'BDD 未完整映射到功能');
const active = state.features.filter(feature => feature.status === 'in-progress');
assert.ok(active.length <= 1, '只能有一个进行中功能');
assert.equal(state.activeFeature, active[0]?.id ?? null, 'activeFeature 不一致');
assert.ok(state.nextFeature === null || byId.has(state.nextFeature), '下一功能不存在');
if (state.executionScope === 'bootstrap-only') {
  assert.ok(state.features.filter(feature => feature.id !== 'H00').every(feature => feature.status === 'not-started'),
    '当前授权仅环境准备，Artifact 功能不能启动');
}

for (const file of [prdPath, ...['AGENTS.md', 'progress.md', 'session-handoff.md'].map(name => path.join(taskDir, name))]) {
  const body = fs.readFileSync(file, 'utf8');
  for (const match of body.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) {
    if (/^(?:https?:|#)/.test(match[1])) continue;
    assert.ok(fs.existsSync(path.resolve(path.dirname(file), match[1].split('#')[0])), `引用不存在：${match[1]}`);
  }
}

const meta = readJson(path.join(prototype, '_d_meta.json'));
assert.equal(meta.primaryDesignSystem, env.designSystem, 'S2 绑定不一致');
const binding = meta.designSystems.find(system => system.slug === env.designSystem);
assert.equal(binding?.namespace, env.designSystemNamespace, 'S2 namespace 不一致');
const ds = path.join(prototype, binding.dsFolder);
const restoredDs = path.resolve(workspace, env.restoredDesignSystem);
for (const name of ['_ds_bundle.js', '_ds_manifest.json', '_ds_prompt.md']) {
  assert.ok(fs.existsSync(path.join(restoredDs, name)), `缺少恢复的 S2 资源：${name}`);
  assert.equal(fs.readFileSync(path.join(ds, name)).compare(fs.readFileSync(path.join(restoredDs, name))), 0,
    `S2 消费副本不一致：${name}`);
}
assert.equal(readJson(path.join(ds, '_ds_manifest.json')).namespace, env.designSystemNamespace);
for (const file of ['vendor/react.development.js', 'vendor/react-dom.development.js', 'vendor/babel.min.js',
  'vendor/editor-tools.js', 'model.js', 'content-model.js', 'content-editor.jsx', 'content-publication.jsx', 'content-reader.jsx']) {
  assert.ok(fs.existsSync(path.join(prototype, file)), `缺少本地基线资源：${file}`);
}
const html = fs.readFileSync(path.join(prototype, 'index.html'), 'utf8');
for (const match of html.matchAll(/<(?:script|link)\b[^>]*\b(?:src|href)=["']([^"']+)["']/g)) {
  if (/^(?:https?:|data:|#)/.test(match[1])) continue;
  assert.ok(fs.existsSync(path.join(prototype, match[1].split('?')[0])), `页面资源缺失：${match[1]}`);
}
for (const file of ['model.js', 'content-model.js', 'copy.js']) run(process.execPath, ['--check', file]);
const require = createRequire(import.meta.url);
const Babel = require(path.join(prototype, 'vendor/babel.min.js'));
for (const file of fs.readdirSync(prototype).filter(name => name.endsWith('.jsx'))) {
  Babel.transform(fs.readFileSync(path.join(prototype, file), 'utf8'), {presets: ['react'], filename: file});
}
console.log(run(process.execPath, ['check-model.cjs']));
console.log(run(process.execPath, ['check-content.cjs']));
console.log(run(process.execPath, ['check-artifact.cjs']));
console.log(run(process.execPath, [path.join(workspace, '.agents/skills/harness-creator/scripts/validate-harness.mjs'),
  '--target', taskDir]));
const python = process.platform === 'win32' ? 'python' : 'python3';
console.log(run(python, ['--version']));
console.log(`环境通过：${env.branch}，PRD ${env.prdVersion}，${state.features.length} 项任务，${bdd.length} 条 BDD。`);
console.log('这是模拟模型与 harness 自动检查；浏览器证据见功能清单，不代表生产 API 验证。');

if (mode === '--serve') {
  await new Promise((resolve, reject) => {
    const probe = net.createServer();
    probe.once('error', error => reject(new Error(`预览端口 ${env.previewPort} 不可用（${error.code}），未终止其他进程。`)));
    probe.listen(env.previewPort, env.previewHost, () => probe.close(resolve));
  });
  const logPath = path.resolve(taskDir, env.previewLog);
  fs.mkdirSync(path.dirname(logPath), {recursive: true});
  const log = fs.createWriteStream(logPath, {flags: 'a'});
  const child = spawn(python, ['-u', '-m', 'http.server', String(env.previewPort), '--bind', env.previewHost,
    '--directory', prototype], {cwd: taskDir, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe']});
  for (const stream of [child.stdout, child.stderr]) stream.on('data', chunk => {log.write(chunk); process.stdout.write(chunk);});
  fs.writeFileSync(path.join(taskDir, '.runtime/server.json'), JSON.stringify({parentPid: process.pid,
    pid: child.pid, port: env.previewPort, directory: prototype, startedAt: new Date().toISOString()}, null, 2));
  console.log(`预览：http://${env.previewHost}:${env.previewPort}/；日志：${logPath}`);
  for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, () => child.kill('SIGTERM'));
  const code = await new Promise((resolve, reject) => {child.once('error', reject); child.once('exit', resolve);});
  log.end();
  process.exitCode = code ?? 0;
}
