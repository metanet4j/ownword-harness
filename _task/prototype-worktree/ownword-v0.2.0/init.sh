#!/usr/bin/env bash
set -euo pipefail

# 只检查已存在的原型环境；不安装依赖，不修改分支或草稿。
TASK_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd -- "$TASK_DIR/../../.." && pwd)"
cd "$TASK_DIR"
case "${1:---check}" in
  --check|--serve) ;;
  *) echo '用法：./init.sh [--check|--serve]' >&2; exit 2 ;;
esac
for command_name in git node python3; do command -v "$command_name" >/dev/null; done
test -f ownword-prototype/.git
bash -n "$TASK_DIR/init.sh"

node - "$WORKSPACE_DIR" <<'JS'
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const state = JSON.parse(fs.readFileSync('feature_list.json', 'utf8'));
const env = state.environment;
const git = (...args) => execFileSync('git', ['-C', env.worktree, ...args], {encoding: 'utf8'}).trim();
assert.equal(git('branch', '--show-current'), env.branch, '原型分支与任务登记不一致');
git('merge-base', '--is-ancestor', env.baselineCommit, 'HEAD');
const prd = fs.readFileSync(path.join(process.argv[2], env.prdSource), 'utf8');
assert.ok(prd.includes(`# Ownword 产品设计 ${env.prdVersion}`), 'PRD 版本不一致');
const meta = JSON.parse(fs.readFileSync(path.join(env.worktree, '_d_meta.json'), 'utf8'));
assert.equal(meta.primaryDesignSystem, env.designSystem, 'S2 绑定不一致');
for (const file of ['index.html', 'vendor/react.development.js', 'vendor/babel.min.js', '_ds/react-spectrum-s2/_ds_bundle.js', '_ds/react-spectrum-s2/_ds_prompt.md', 'vendor/editor-tools.js', 'content-model.js', 'content-editor.jsx', 'content-publication.jsx', 'content-reader.jsx']) {
  assert.ok(fs.existsSync(path.join(env.worktree, file)), `缺少本地资源：${file}`);
}
const ids = new Set(state.features.map(f => f.id));
assert.equal(ids.size, state.features.length, '功能编号重复');
for (const f of state.features) {
  assert.ok(state.allowedStatuses.includes(f.status), `无效状态：${f.id}`);
  for (const id of f.dependencies) assert.ok(ids.has(id), `缺少依赖：${id}`);
  for (const ref of f.acceptanceRefs || []) assert.ok(prd.includes(`| ${ref} |`), `缺少验收：${ref}`);
}
const active = state.features.filter(f => f.status === 'in-progress');
assert.ok(active.length <= 1, '只能有一个进行中功能');
assert.equal(state.activeFeature, active[0]?.id ?? null, '当前功能与状态不一致');
console.log(`环境通过：${env.branch}，PRD ${env.prdVersion}，${state.features.length} 项任务`);
JS

# 检查原型源码语法、状态不变量、Markdown 边界与双语文案；浏览器证据另列。
node --check ownword-prototype/model.js
node --check ownword-prototype/copy.js
node ownword-prototype/check-model.cjs
node ownword-prototype/check-content.cjs
node ownword-prototype/check-markdown.mjs
node ownword-prototype/check-copy.cjs
python3 ownword-prototype/check-tokens.py
node <<'JS'
const fs=require('node:fs'),Babel=require('./ownword-prototype/vendor/babel.min.js');
for(const file of fs.readdirSync('ownword-prototype').filter(f=>f.endsWith('.jsx'))) {
  Babel.transform(fs.readFileSync('ownword-prototype/'+file,'utf8'),{presets:['react'],filename:file});
}
console.log('全部 JSX 源码语法检查通过');
JS
node "$WORKSPACE_DIR/.agents/skills/harness-creator/scripts/validate-harness.mjs" --target "$TASK_DIR"

if [[ "${1:---check}" == '--serve' ]]; then
  PREVIEW_PORT="$(node -p "require('./feature_list.json').environment.previewPort")"
  mkdir -p .runtime
  echo "预览：http://127.0.0.1:$PREVIEW_PORT/；日志：$TASK_DIR/.runtime/preview.log"
  python3 -u -m http.server "$PREVIEW_PORT" --bind 127.0.0.1 --directory "$TASK_DIR/ownword-prototype" 2>&1 | tee -a .runtime/preview.log
else
  echo '检查通过。运行 ./init.sh --serve 启动预览；下一步见 session-handoff.md。'
fi
