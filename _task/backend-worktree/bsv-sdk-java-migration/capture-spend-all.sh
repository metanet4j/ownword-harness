#!/usr/bin/env bash
# spend 批 9 个标准双侧局部的统一采集：重采 + 篡改门禁 + 全量前置检查。
# 由主代理在所有人停笔后的独占窗口运行（整个脚本应在一次 ./lock.sh 内执行）：
#   ./lock.sh ./capture-spend-all.sh [日期标签]
# 运行目录形如 .cache/evidence/<局部>-final-<标签>，脚本会拒绝非空目录。
set -uo pipefail
TASK="$(cd "$(dirname "$0")" && pwd)"
cd "$TASK"
TAG="${1:-20260930}"
LOCALS=(spend-chronicle-vector spend-codeseparator spend-complex lrshiftnum chronicle spend-verifier spend-core spend-additional normative-vectors)
PREFLIGHT=".cache/evidence/preflight-spend-final-${TAG}.json"
failed=()

for L in "${LOCALS[@]}"; do
  RUN="$TASK/.cache/evidence/$L-final-$TAG"
  if [ -d "$RUN" ] && [ -n "$(ls -A "$RUN" 2>/dev/null)" ]; then
    echo "SKIP $L：运行目录非空 $RUN"; failed+=("$L:run-dir-not-empty"); continue
  fi
  echo "=== recapture $L ==="
  if python3 recapture-local.py --name "$L" --run "$RUN" --update > "$RUN.log" 2>&1; then
    tail -1 "$RUN.log"
    echo "=== tamper $L ==="
    if python3 local-evidence-gate.py tamper --name "$L" 2>&1 | tail -3; then :; else failed+=("$L:tamper"); fi
  else
    echo "RECAPTURE FAILED $L"; tail -12 "$RUN.log"; failed+=("$L:recapture")
  fi
done

echo "=== preflight ==="
if python3 full-evidence-preflight.py --output "$PREFLIGHT" 2>&1 | tail -3; then
  python3 - "$PREFLIGHT" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
names = ['spend-chronicle-vector','spend-codeseparator','spend-complex','lrshiftnum','chronicle',
         'spend-verifier','spend-core','spend-additional','normative-vectors']
for row in d['locals']:
    if row['name'] in names:
        print(row['name'], 'planValid', row['planValid'], 'capture', row.get('currentCaptureVerified'),
              row.get('planError', ''), row.get('captureError', ''))
print('planErrors', d['planErrors'])
PY
else
  failed+=("preflight")
fi

echo "=== summary ==="
if [ ${#failed[@]} -eq 0 ]; then echo "ALL OK"; else printf 'FAILED: %s\n' "${failed[@]}"; fi
