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
const readJson = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const run = (command, args, cwd = workspace) => execFileSync(command, args, {
  cwd, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe']
}).trim();

try {
  assert.ok(['--plan', '--check', '--serve'].includes(mode) && process.argv.length <= 3,
    '用法：node bootstrap.mjs [--plan|--check|--serve]');
  const state = readJson(path.join(taskDir, 'feature_list.json'));
  const env = state.environment;
  const prototype = path.resolve(taskDir, env.worktree);
  const sourceDir = path.resolve(workspace, env.sourceRepository);
  const sourceGit = (...args) => run('git', ['-C', sourceDir, ...args]);
  const git = (...args) => run('git', ['-C', prototype, ...args]);
  const prdPath = path.resolve(workspace, env.prdSource);
  const prd = fs.readFileSync(prdPath, 'utf8');
  assert.ok(prd.includes(`# Ownword 产品设计 ${env.prdVersion}`), 'PRD 版本不一致');
  assert.ok(fs.existsSync(path.resolve(workspace, state.designReview.source)), '缺少设计审查报告');
  const bdd = [...prd.matchAll(/^\| (P\d{2}-[A-Z]) \|/gm)].map(match => match[1]);
  assert.equal(bdd.length, 32, '验收场景数与当前 PRD 不一致');
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
    for (const dep of byId.get(id).dependencies) visit(dep, new Set([...chain, id]));
    visited.add(id);
  }
  for (const id of byId.keys()) visit(id);
  assert.deepEqual([...covered].sort(), [...bdd].sort(), 'BDD 未完整映射');
  const active = state.features.filter(feature => feature.status === 'in-progress');
  assert.ok(active.length <= 1, '只能有一个进行中功能');
  assert.equal(state.activeFeature, active[0]?.id ?? null, 'activeFeature 不一致');
  assert.ok(state.nextFeature === null || byId.has(state.nextFeature), '下一功能不存在');
  for (const file of [prdPath, ...['AGENTS.md', 'progress.md', 'session-handoff.md'].map(name => path.join(taskDir, name))]) {
    const body = fs.readFileSync(file, 'utf8');
    for (const match of body.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) {
      if (/^(?:https?:|#)/.test(match[1])) continue;
      assert.ok(fs.existsSync(path.resolve(path.dirname(file), match[1].split('#')[0])), `引用不存在：${match[1]}`);
    }
  }
  console.log(run(process.execPath, [path.join(workspace, '.agents/skills/harness-creator/scripts/validate-harness.mjs'), '--target', taskDir]));
  if (mode === '--plan') {
    console.log(`任务登记通过：${state.features.length} 项任务、${bdd.length} 条 BDD；此检查不表示 worktree 或页面可用。`);
    process.exit(0);
  }

  try { sourceGit('cat-file', '-e', `${env.baselineCommit}^{commit}`); }
  catch { throw new Error(`缺少 v0.3.0 基线 Git 对象 ${env.baselineCommit}；请先恢复实际源码或可取得的远端分支。`); }
  assert.ok(fs.existsSync(path.join(prototype, '.git')) && fs.statSync(path.join(prototype, '.git')).isFile(),
    '尚未创建独立原型 worktree');
  assert.equal(git('branch', '--show-current'), env.branch, '实际分支与登记不一致');
  git('merge-base', '--is-ancestor', env.baselineCommit, 'HEAD');
  assert.equal(fs.realpathSync(git('rev-parse', '--path-format=absolute', '--git-common-dir')),
    fs.realpathSync(sourceGit('rev-parse', '--path-format=absolute', '--git-common-dir')), 'worktree 来源不一致');

  const meta = readJson(path.join(prototype, '_d_meta.json'));
  assert.equal(meta.primaryDesignSystem, env.designSystem, 'S2 主绑定不一致');
  const binding = meta.designSystems.find(system => system.slug === env.designSystem);
  assert.equal(binding?.namespace, env.designSystemNamespace, 'S2 namespace 不一致');
  const ds = path.join(prototype, binding.dsFolder);
  for (const name of ['_ds_bundle.js', '_ds_manifest.json', '_ds_prompt.md']) {
    const relative = `${binding.dsFolder}/${name}`;
    const baseline = execFileSync('git', ['-C', sourceDir, 'show', `${env.baselineCommit}:${relative}`],
      {maxBuffer: 16 * 1024 * 1024});
    assert.equal(fs.readFileSync(path.join(ds, name)).compare(baseline), 0, `S2 运行时偏离 v0.3.0 基线：${name}`);
  }
  const html = fs.readFileSync(path.join(prototype, 'index.html'), 'utf8');
  for (const match of html.matchAll(/<(?:script|link)\b[^>]*\b(?:src|href)=["']([^"']+)["']/g)) {
    if (/^(?:https?:|data:|#)/.test(match[1])) continue;
    assert.ok(fs.existsSync(path.join(prototype, match[1].split('?')[0])), `页面资源缺失：${match[1]}`);
  }
  console.log(run(process.execPath, ['build-prototype.mjs', '--check'], prototype));
  const require = createRequire(import.meta.url);
  const Babel = require(path.join(prototype, 'vendor/babel.min.js'));
  for (const file of fs.readdirSync(prototype)) {
    if (/\.(?:js|cjs)$/.test(file)) run(process.execPath, ['--check', file], prototype);
    if (file.endsWith('.jsx')) Babel.transform(fs.readFileSync(path.join(prototype, file), 'utf8'), {presets: ['react'], filename: file});
  }
  for (const file of ['check-model.cjs', 'check-content.cjs', 'check-artifact.cjs', 'check-ui.cjs']) {
    assert.ok(fs.existsSync(path.join(prototype, file)), `缺少继承检查：${file}`);
    console.log(run(process.execPath, [file], prototype));
  }
  if (fs.existsSync(path.join(prototype, 'check-homepage.cjs'))) console.log(run(process.execPath, ['check-homepage.cjs'], prototype));
  console.log(`环境检查通过：${env.branch}；继承 v0.3.0 ${env.baselineCommit}。浏览器及功能证据另行登记。`);
  if (mode === '--serve') {
    await new Promise((resolve, reject) => {
      const probe = net.createServer();
      probe.once('error', error => reject(new Error(`预览端口 ${env.previewPort} 不可用：${error.code}，未终止其他进程。`)));
      probe.listen(env.previewPort, env.previewHost, () => probe.close(resolve));
    });
    const logPath = path.resolve(taskDir, env.previewLog);
    fs.mkdirSync(path.dirname(logPath), {recursive: true});
    const log = fs.createWriteStream(logPath, {flags: 'a'});
    const python = process.platform === 'win32' ? 'python' : 'python3';
    const child = spawn(python, ['-u', path.join(taskDir, 'preview-server.py'), String(env.previewPort), '--bind', env.previewHost,
      '--directory', prototype], {cwd: taskDir, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe']});
    for (const stream of [child.stdout, child.stderr]) stream.on('data', chunk => {log.write(chunk); process.stdout.write(chunk);});
    fs.writeFileSync(path.join(taskDir, '.runtime/server.json'), JSON.stringify({parentPid: process.pid, pid: child.pid, port: env.previewPort, directory: prototype, startedAt: new Date().toISOString()}, null, 2));
    console.log(`预览：http://${env.previewHost}:${env.previewPort}/；日志：${logPath}`);
    for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, () => child.kill('SIGTERM'));
    const code = await new Promise((resolve, reject) => {child.once('error', reject); child.once('exit', resolve);});
    log.end();
    process.exitCode = code ?? 0;
  }
} catch (error) {
  console.error(`检查未通过：${error.message}`);
  process.exitCode = 1;
}
