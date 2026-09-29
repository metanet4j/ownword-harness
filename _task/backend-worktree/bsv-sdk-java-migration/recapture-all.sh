#!/usr/bin/env bash
# 收尾统一重采：所有登记了 capture 适配器的标准局部，在同一 Java 来源下重采并跑篡改门禁。
# 用法：./recapture-all.sh <日期标签> [局部名...]      （不传局部名则处理全部）
set -uo pipefail
TASK="$(cd "$(dirname "$0")" && pwd)"
cd "$TASK"
LABEL="${1:?用法: ./recapture-all.sh <日期标签> [局部名...]}"
shift || true
if [ "$#" -gt 0 ]; then
  NAMES=("$@")
else
  mapfile -t NAMES < <(python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path('full-evidence-locals.json').read_text())
for item in data['locals']:
    if item.get('capture') and item.get('captureKind') != 'specialized-local':
        print(item['name'])
PY
)
fi
failed=()
for name in "${NAMES[@]}"; do
  run=".cache/evidence/${name}-standard-${LABEL}"
  rm -rf "$run"
  echo "=== $name ==="
  if ! ./lock.sh python3 recapture-local.py --name "$name" --run "$run" --update 2>&1 | tail -1; then
    failed+=("$name:recapture")
    continue
  fi
  if ! ./lock.sh python3 local-evidence-gate.py tamper --name "$name" 2>&1 | tail -1; then
    failed+=("$name:tamper")
  fi
done
echo "=== 汇总 ==="
if [ "${#failed[@]}" -gt 0 ]; then
  printf '失败：%s\n' "${failed[@]}"
  exit 1
fi
echo "全部局部重采与篡改门禁通过"
