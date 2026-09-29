#!/usr/bin/env bash
# 结构覆盖率缺口两局部的采集清单（统一窗口内执行；每条命令都必须走 ./lock.sh）。
# 用法：统一窗口内执行  bash collect-gap-locals-20260929.sh
set -euo pipefail
TASK="$(cd "$(dirname "$0")" && pwd)"
cd "$TASK"

for name in chronicle-opcodes simplified-fetch-transport-additional; do
  run=".cache/evidence/${name}-standard-20260929"
  echo "=== ${name}: recapture -> ${run}"
  ./lock.sh python3 recapture-local.py --name "$name" --run "$run" --update
  echo "=== ${name}: tamper"
  ./lock.sh python3 local-evidence-gate.py tamper --name "$name"
done

echo "=== 聚焦 Java clean test"
./lock.sh ./mvn.sh -f metanet4j-bsv-sdk/pom.xml clean test \
  -Dtest='ChronicleOpcodesTest,SimplifiedFetchTransportAdditionalTest'

echo "=== 两条既有无关测试（回归）"
./lock.sh ./mvn.sh -f metanet4j-bsv-sdk/pom.xml clean test -Dtest='ChronicleOpcodesTest'
./lock.sh ./mvn.sh -f metanet4j-bsv-sdk/pom.xml clean test -Dtest='SimplifiedFetchTransportAdditionalTest'

echo "=== preflight"
./lock.sh python3 full-evidence-preflight.py --output .cache/evidence/preflight-gap-locals-20260929.json
