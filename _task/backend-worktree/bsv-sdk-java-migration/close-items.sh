#!/usr/bin/env bash
# 最终窗口后：对计划已完整的实现事项逐个出任务级对照报告（local-task-parity.py）。
# 前置：Java 工作树干净且所有相关局部已在同一来源下重采。用法：./close-items.sh <日期标签>
set -uo pipefail
TASK="$(cd "$(dirname "$0")" && pwd)"
cd "$TASK"
LABEL="${1:?用法: ./close-items.sh <日期标签>}"
python3 - "$LABEL" <<'PY' > /tmp/close-items-plan.txt
import json, sys
from pathlib import Path
report = json.loads(Path('item-locals.json').read_text())
label = sys.argv[1]
for item, row in sorted(report.items()):
    if row['uncoveredCases']:
        continue
    locals_ = list(row['locals'])
    if not locals_:
        continue
    print(item, label, len(locals_), *locals_)
PY
ok=0; failed=()
while read -r item label count rest; do
  # shellcheck disable=SC2086
  set -- $rest
  args=()
  for name in "$@"; do args+=(--local "$name"); done
  out=".cache/evidence/${item}-final-${label}"
  echo "=== $item（$count 个局部） ==="
  if python3 local-task-parity.py --task "$item" "${args[@]}" --output "$out" 2>&1 | tail -1; then
    ok=$((ok+1))
  else
    failed+=("$item")
  fi
done < /tmp/close-items-plan.txt
echo "=== 汇总 ==="
echo "成功 $ok 个事项；失败 ${#failed[@]} 个：${failed[*]:-无}"
[ "${#failed[@]}" -eq 0 ]
