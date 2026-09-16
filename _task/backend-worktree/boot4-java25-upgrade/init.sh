#!/usr/bin/env bash
# init.sh — metanet4j 升级任务的环境与状态自检
#
#   ./init.sh          环境 + 仓库状态（秒级，不触发构建）
#   ./init.sh --full   追加真实构建与测试（P2 之前预期失败，属正常进度）
#
# 退出码：0 = 通过；1 = 有必须先修的异常
#
# fail-fast：本脚本不用 `set -e`（自检要把所有项都报出来），而是在结尾以退出码汇总；
# 逐项判定只设 fail 标记，不做提前退出。构建步骤（--full）在子 shell 中执行并回报状态。
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAVA_HOME_EXPECTED="$HOME/.sdkman/candidates/java/25.0.4.1-tem"
MVN_BIN="$HOME/.sdkman/candidates/maven/3.9.16/bin/mvn"
SETTINGS="$HOME/.m2/metanet4j-settings.xml"
LOCAL_REPO="$HOME/.m2/metanet4j"
REPOS=(metanet4j-parent metanet4j-base metanet4j-sdk metanet4j-component)
COMPOSE_PROJECT="ownword-infra"
FULL=0
[ "${1:-}" = "--full" ] && FULL=1

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
for f in AGENTS.md feature_list.json progress.md session-handoff.md init.sh doc/升级计划-Boot4-Java25.md; do
  [ -e "$ROOT/$f" ] && ok "$f" || bad "$f 缺失"
done

sec "3. 四个子仓库状态"
for r in "${REPOS[@]}"; do
  d="$ROOT/$r"
  # worktree 的 .git 是文件（gitdir 指针），只能用 git 自身判定
  if ! git -C "$d" rev-parse --git-dir >/dev/null 2>&1; then bad "$r 不是 git 仓库"; continue; fi
  br="$(git -C "$d" branch --show-current 2>/dev/null)"
  dirt="$(git -C "$d" status --porcelain 2>/dev/null | wc -l)"
  if [ "$br" = "feature/java21" ]; then
    [ "$dirt" = "0" ] && ok "$r：分支 $br，工作区干净" || warn "$r：分支 $br，有 $dirt 个未提交改动"
  else
    warn "$r：分支为 $br（预期 feature/java21）"
  fi
done

sec "4. 共享中间件（ownword/infra）"
if command -v docker >/dev/null 2>&1; then
  running="$(docker ps --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" --format '{{.Names}}' 2>/dev/null | wc -l)"
  healthy="$(docker ps --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" --format '{{.Status}}' 2>/dev/null | grep -c healthy)"
  if [ "$running" = "5" ] && [ "$healthy" = "5" ]; then
    ok "五个容器运行中且全部 healthy"
  else
    warn "容器状态：运行 $running 个，healthy $healthy 个（应各为 5）→ 运行 'cd $HOME/ownword/infra && ./up.sh'"
  fi
  for p in 27017 9200 9092 6379 3306; do
    timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/$p" 2>/dev/null \
      && ok "端口 $p 可连接" || warn "端口 $p 不可连接"
  done
else
  warn "docker 不可用，跳过中间件检查"
fi

sec "5. 阶段进度速览"
if command -v python3 >/dev/null 2>&1; then
  python3 - "$ROOT/feature_list.json" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception as e:
    print(f"  [FAIL] feature_list.json 解析失败：{e}")
    sys.exit(1)
print(f"  activeItem = {d.get('activeItem')}")
for f in d.get("features", []):
    mark = {"done": "[x]", "in-progress": "[~]", "blocked": "[!]", "not-started": "[ ]"}.get(f.get("status"), "[?]")
    print(f"  {mark} {f['id']:<22} {f.get('status')}")
PY
fi

if [ "$FULL" = "1" ]; then
  sec "6. 真实构建与测试（--full）"
  echo "  说明：这是 build 级校验（clean package），P2 完成前预期失败（当前 parent 仍是 Boot 2.3.2 + lombok 1.18.20，JDK 25 下编译崩）。"
  install_and_test() {
    local dir="$1"; shift
    echo "  --- $dir：$*"
    ( cd "$ROOT/$dir" && JAVA_HOME="$JAVA_HOME_EXPECTED" "$MVN_BIN" -s "$SETTINGS" -B "$@" 2>&1 | tail -12 )
    return "${PIPESTATUS[0]}"
  }
  if install_and_test metanet4j-parent -N install; then ok "parent install"; else warn "parent install 失败（见上）"; fi
  if install_and_test metanet4j-base clean test; then ok "base test"; else warn "base test 失败（见上）"; fi
  if install_and_test metanet4j-sdk clean test; then ok "sdk test"; else warn "sdk test 失败（见上）"; fi
  if install_and_test metanet4j-component clean package; then ok "component package"; else warn "component package 失败（见上）"; fi

  sec "6b. 分模块测试执行数（不接受总数口径）"
  found=0
  for r in "${REPOS[@]}"; do
    for rep in "$ROOT/$r"/target/surefire-reports "$ROOT/$r"/*/target/surefire-reports; do
      [ -d "$rep" ] || continue
      line="$(grep -h 'Tests run' "$rep"/*.txt 2>/dev/null | tail -1)"
      [ -n "$line" ] && { printf '  %-58s %s\n' "${rep#$ROOT/}" "$line"; found=1; }
    done
  done
  [ "$found" = "0" ] && warn "未找到 surefire 报告（构建未到测试阶段）"
  grep -rq 'contextLoads' "$ROOT"/*/target/surefire-reports/*.txt 2>/dev/null \
    && ok "contextLoads 出现在 surefire 报告（基类上下文用例真的执行了）" \
    || warn "contextLoads 未出现在 surefire 报告（上下文冒烟未执行）"
fi

sec "结论"
if [ "$fail" = "0" ]; then
  echo "  自检通过。下一步见 session-handoff.md 的「唯一下一步」。"
else
  echo "  自检发现必须先修的问题（上面标 FAIL 的项）。"
fi
exit "$fail"
