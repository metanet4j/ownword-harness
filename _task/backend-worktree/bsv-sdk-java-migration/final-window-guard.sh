#!/usr/bin/env bash
# 最终窗口前置守卫：只有全部通过才允许开始统一重采（任一失败即退出非零，不要绕过）。
set -u
cd "$(dirname "$0")"
QUIET_MINUTES="${1:-10}"
fail=0
note() { printf '%-46s %s\n' "$1" "$2"; }

# 1) 静默：最近 N 分钟内不得有人改 Java 源码
recent=$(find metanet4j-bsv-sdk/src -newermt "-${QUIET_MINUTES} minutes" -type f 2>/dev/null | head -3)
if [ -n "$recent" ]; then note "1 静默检查（${QUIET_MINUTES} 分钟内无改动）" "失败"; echo "$recent" | sed 's/^/     /'; fail=1
else note "1 静默检查（${QUIET_MINUTES} 分钟内无改动）" "通过"; fi

# 2) 编译：整个测试模块必须可编译
if ./lock.sh ./mvn.sh -f metanet4j-bsv-sdk/pom.xml test-compile >/tmp/guard-compile.log 2>&1; then
  note "2 test-compile" "通过"
else
  note "2 test-compile" "失败"; grep -oE "ERROR\] [^ ]+\.java:\[[0-9]+,[0-9]+\]" /tmp/guard-compile.log | sort -u | head -3 | sed 's/^/     /'; fail=1
fi

# 3) 冻结计划结构
if out=$(python3 validate-plans.py 2>&1 | tail -1) && echo "$out" | grep -q '"failed": 0'; then note "3 validate-plans" "通过 $out"
else note "3 validate-plans" "失败 $out"; fail=1; fi

# 4) 全量分派表
out=$(python3 build-full-run-probes.py 2>&1 | tail -1)
if echo "$out" | grep -q '"unresolved": 0'; then note "4 全量分派表" "通过 $out"; else note "4 全量分派表" "失败 $out"; fail=1; fi

# 5) 覆盖率：全部冻结用例都要有计划
cov=$(python3 - <<'PY'
import json
from pathlib import Path
catalog = json.loads(Path('module-tests.json').read_text())
config = json.loads(Path('full-evidence-locals.json').read_text())
planned = set()
for local in config['locals']:
    p = Path(local['input_plan'])
    if p.exists():
        try: planned |= set(json.loads(p.read_text()))
        except Exception: pass
allc = {c['id'] for f in catalog['files'] for c in f['cases']}
print(f'{len(planned)} {len(allc)}')
PY
)
set -- $cov
if [ "$1" = "$2" ]; then note "5 计划覆盖率" "通过 $1/$2"; else note "5 计划覆盖率" "失败 $1/$2（缺 $(( $2 - $1 )) 例）"; fail=1; fi

# 6) SDK 工作树：全部改动已提交（来源可冻结）
if [ -z "$(cd metanet4j-bsv-sdk && git status --porcelain)" ]; then note "6 SDK 工作树已提交" "通过"
else note "6 SDK 工作树已提交" "失败（未提交改动 $(cd metanet4j-bsv-sdk && git status --porcelain | wc -l) 个）"; fail=1; fi

echo
if [ "$fail" -eq 0 ]; then
  cat <<'NEXT'
守卫通过，可以开窗。按运行手册第五节执行：
  cd metanet4j-bsv-sdk && git add -A && git commit -m "test(migration): 冻结来源" && cd ..
  ./recapture-all.sh final-$(date +%Y%m%d)
  ./lock.sh python3 full-evidence-preflight.py --output .cache/evidence/preflight-final.json
NEXT
  exit 0
fi
echo "守卫未通过：先修掉上面失败项，再开窗。"
exit 1
