#!/usr/bin/env bash
# init.sh — metanet4j 当前任务的环境与状态自检
#
#   ./init.sh          环境 + 仓库 + feature 状态（不触发构建）
# 构建与测试使用 feature_list.json.planDoc 的严格验收命令。
#
# 退出码：0 = 通过；1 = 有必须先修的异常
#
# 自检汇总所有异常，逐项判定设置 fail 标记，结尾返回非零。
set -uo pipefail

if [ "$#" -ne 0 ]; then
  printf '不支持参数 %s；init.sh 仅自检，构建／测试入口见 feature_list.json.planDoc。\n' "$*" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAVA_HOME_EXPECTED="$HOME/.sdkman/candidates/java/25.0.4.1-tem"
MVN_BIN="$HOME/.sdkman/candidates/maven/3.9.16/bin/mvn"
SETTINGS="$HOME/.m2/metanet4j-settings.xml"
LOCAL_REPO="$HOME/.m2/metanet4j"
REPOS=(metanet4j-parent metanet4j-base metanet4j-sdk metanet4j-component)
COMPOSE_PROJECT="ownword-infra"
EXPECTED_BRANCH="feature/bsv-sdk-replace"

fail=0
ok()   { printf '  [OK]   %s\n' "$1"; }
bad()  { printf '  [FAIL] %s\n' "$1"; fail=1; }
warn() { printf '  [WARN] %s\n' "$1"; }
sec()  { printf '\n=== %s ===\n' "$1"; }

sec "0. 工作目录"
printf '  ROOT=%s\n' "$ROOT"

sec "1. 工具链（任务内锁定，全局不动）"
[ -x "$JAVA_HOME_EXPECTED/bin/java" ] \
  && ok "JDK 25 存在：$("$JAVA_HOME_EXPECTED/bin/java" -version 2>&1 | head -1)" \
  || bad "JDK 25 缺失：$JAVA_HOME_EXPECTED"
[ -x "$MVN_BIN" ] && ok "Maven 3.9.16 存在" || bad "Maven 3.9.16 缺失：$MVN_BIN"
[ -f "$SETTINGS" ] && ok "settings.xml 存在：$SETTINGS" || bad "settings.xml 缺失：$SETTINGS"
[ -d "$LOCAL_REPO" ] && ok "独立本地仓库存在（$(du -sh "$LOCAL_REPO" 2>/dev/null | cut -f1)）" || bad "本地仓库缺失：$LOCAL_REPO"

if [ -x "$MVN_BIN" ]; then
  JAVA_HOME="$JAVA_HOME_EXPECTED" "$MVN_BIN" -s "$SETTINGS" -v 2>/dev/null \
    | grep -q 'Java version: 25' \
    && ok "Maven 实际运行在 JDK 25 上" \
    || bad "Maven 未运行在 JDK 25 上（检查 JAVA_HOME 是否显式传入）"
fi

GLOBAL_JAVA="$(readlink -f "$HOME/.sdkman/candidates/java/current" 2>/dev/null | xargs -r basename)"
GLOBAL_MVN="$(readlink -f "$HOME/.sdkman/candidates/maven/current" 2>/dev/null | xargs -r basename)"
case "$GLOBAL_JAVA" in
  25.0.4.1-tem) bad "全局 java 被改成了 JDK 25（违反版本隔离约束）" ;;
  *) ok "全局 java 默认未被改动：${GLOBAL_JAVA:-未知}" ;;
esac
[ "$GLOBAL_MVN" = "3.9.16" ] \
  && bad "全局 maven 被改成了 3.9.16（违反版本隔离约束）" \
  || ok "全局 maven 默认未被改动：${GLOBAL_MVN:-未知}"

sec "2. 任务文件"
for f in ../AGENTS.md ../mvn-command.md AGENTS.md feature_list.json progress.md session-handoff.md init.sh doc/升级计划-Boot4-Java25.md; do
  [ -e "$ROOT/$f" ] && ok "$f" || bad "$f 缺失"
done

sec "3. 四个子仓库状态"
for r in "${REPOS[@]}"; do
  d="$ROOT/$r"
  # worktree 的 .git 是文件（gitdir 指针），只能用 git 自身判定
  if ! git -C "$d" rev-parse --git-dir >/dev/null 2>&1; then bad "$r 不是 git 仓库"; continue; fi
  br="$(git -C "$d" branch --show-current 2>/dev/null)"
  dirt="$(git -C "$d" status --porcelain 2>/dev/null | wc -l)"
  if [ "$br" = "$EXPECTED_BRANCH" ]; then
    [ "$dirt" = "0" ] && ok "$r：分支 $br，工作区干净" || warn "$r：分支 $br，有 $dirt 个未提交改动"
  else
    bad "$r：分支为 $br（预期 $EXPECTED_BRANCH）"
  fi
done

sec "4. 共享中间件（ownword/infra）"
if command -v docker >/dev/null 2>&1; then
  if container_status="$(docker ps --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" --format '{{.Status}}' 2>/dev/null)"; then
    running="$(printf '%s\n' "$container_status" | grep -c . || true)"
    healthy="$(printf '%s\n' "$container_status" | grep -c '(healthy)' || true)"
    if [ "$running" = "5" ] && [ "$healthy" = "5" ]; then
      ok "五个容器运行中且全部 healthy"
    else
      warn "容器状态：运行 $running 个，healthy $healthy 个（应各为 5）；仅阻塞集成，集成前使用 ownword/infra/up.sh"
    fi
  else
    warn "无法读取 Docker 状态（可能是执行权限限制）；集成前在宿主核查，不推断容器已停止"
  fi
  for p in 27017 9200 9092 6379 3306; do
    timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/$p" 2>/dev/null \
      && ok "端口 $p 可连接" || warn "端口 $p 不可连接"
  done
else
  warn "docker 不可用，跳过中间件检查"
fi

sec "5. 当前计划与执行状态"
if command -v python3 >/dev/null 2>&1; then
  if python3 - "$ROOT" <<'PY'
import json, sys
from pathlib import Path

try:
    root = Path(sys.argv[1])
    d = json.loads((root / 'feature_list.json').read_text())
    for key in ('planDoc', 'upgradePlanDoc', 'testPlanDoc'):
        value = d.get(key)
        if not isinstance(value, str) or not (root / value).is_file():
            raise ValueError(f'{key} 未指定有效文件：{value}')
    if d.get('authorization', {}).get('status') != 'approved':
        raise ValueError('当前计划未记录明确实施授权')
    features = d['features']
    by_id = {f['id']: f for f in features}
    if len(by_id) != len(features):
        raise ValueError('feature ID 重复')
    allowed = set(d['allowedStatuses'])
    visiting, visited = set(), set()

    def visit(fid):
        if fid in visiting:
            raise ValueError(f'feature 依赖有环：{fid}')
        if fid in visited:
            return
        if fid not in by_id:
            raise ValueError(f'依赖 feature 不存在：{fid}')
        visiting.add(fid)
        f = by_id[fid]
        if f['status'] not in allowed:
            raise ValueError(f'未知状态：{fid}')
        for dep in f.get('dependencies', []):
            visit(dep)
            if f['status'] in ('in-progress', 'done') and by_id[dep]['status'] != 'done':
                raise ValueError(f'{fid} 的依赖 {dep} 未完成')
        if f['status'] == 'done' and not f.get('evidence'):
            raise ValueError(f'{fid} 完成但无证据')
        visiting.remove(fid)
        visited.add(fid)

    for fid in by_id:
        visit(fid)
    current = [f['id'] for f in features if f['status'] == 'in-progress']
    expected = [] if d.get('activeItem') is None else [d['activeItem']]
    if current != expected:
        raise ValueError(f'activeItem 与唯一执行项不符：{current} / {expected}')
    if d.get('nextItem') is not None and d['nextItem'] not in by_id:
        raise ValueError('nextItem 不存在')
    stages = d['stages']
    stages_by_id = {s['id']: s for s in stages}
    if len(stages_by_id) != len(stages):
        raise ValueError('阶段 ID 重复')
    assigned = []
    for stage in stages:
        children = [by_id[fid] for fid in stage['featureIds']]
        if not children or any(f.get('stageId') != stage['id'] for f in children):
            raise ValueError(f"阶段分配不符：{stage['id']}")
        assigned.extend(f['id'] for f in children)
        counts = {'total': len(children), 'done': sum(f['status'] == 'done' for f in children)}
        if stage['progress'] != counts:
            raise ValueError(f"阶段计数不符：{stage['id']}")
        if any(f['status'] == 'blocked' for f in children):
            status = 'blocked'
        elif counts['done'] == counts['total']:
            status = 'done'
        elif any(f['status'] in ('done', 'in-progress') for f in children):
            # 阶段内有任意项已开工或已完成：阶段为 in-progress（门禁仍由各子项承担）
            status = 'in-progress'
        else:
            status = 'not-started'
        if stage['status'] != status:
            raise ValueError(f"阶段状态不符：{stage['id']} / {status}")
        for dep in stage.get('dependencies', []):
            prerequisite = stages_by_id.get(dep) or by_id.get(dep)
            if prerequisite is None:
                raise ValueError(f'阶段依赖不存在：{dep}')
            if status != 'not-started' and prerequisite['status'] != 'done':
                raise ValueError(f"阶段 {stage['id']} 的前置门禁 {dep} 未完成")
    leaves = {f['id'] for f in features if 'stageId' in f}
    if len(assigned) != len(set(assigned)) or set(assigned) != leaves:
        raise ValueError('阶段子项重复或遗漏')
    print(f"  [OK] 当前计划：{d['planDoc']}")
    print(f"  activeItem = {d.get('activeItem')}，nextItem = {d.get('nextItem')}")
    for stage in stages:
        print(f"  {stage['id']}: {stage['status']}，{stage['progress']['done']}/{stage['progress']['total']}")
    print('  [OK] feature 状态、依赖、完成证据及阶段门禁一致')
except (ValueError, KeyError, TypeError, OSError) as e:
    print(f'  [FAIL] 当前计划或执行状态异常：{e}')
    sys.exit(1)
PY
  then
    ok "执行状态检查通过"
  else
    bad "执行状态检查失败"
  fi
else
  bad "python3 不可用，无法核对执行状态"
fi

sec "结论"
if [ "$fail" = "0" ]; then
  echo "  自检通过。下一步见 session-handoff.md 的「唯一下一步」。"
else
  echo "  自检发现必须先修的问题（上面标 FAIL 的项）。"
fi
exit "$fail"
