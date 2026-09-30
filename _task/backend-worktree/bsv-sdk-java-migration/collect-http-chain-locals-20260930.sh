#!/usr/bin/env bash
# http-chain 五个新增局部的统一采集：先在同一把锁内做编译门禁，通过后按登记串行采集并逐个跑篡改门禁。
# 用法：bash collect-http-chain-locals-20260930.sh
set -uo pipefail
cd "$(dirname "$0")"

LOCALS=(block-headers-service whats-on-chain-additional whats-on-chain-chain-tracker default-http-client default-http-client-additional)

for attempt in $(seq 1 20); do
  stamp=$(date +%Y%m%d-%H%M%S)
  specs=()
  for name in "${LOCALS[@]}"; do specs+=("${name}:.cache/evidence/${name}-standard-${stamp}"); done
  echo "=== attempt $attempt $(date +%H:%M:%S) ==="
  ./lock.sh bash -c '
    set -uo pipefail
    if ! ./mvn.sh -f metanet4j-bsv-sdk/pom.xml clean test-compile > /tmp/http-chain-gate.log 2>&1; then
      echo GATE_FAIL
      grep -m3 "^\[ERROR\] /home" /tmp/http-chain-gate.log
      exit 9
    fi
    echo GATE_OK
    for spec in "$@"; do
      name="${spec%%:*}"; dir="${spec#*:}"
      python3 recapture-local.py --name "$name" --run "$dir" --update || { echo "CAPTURE_FAIL $name"; exit 10; }
      python3 local-evidence-gate.py tamper --name "$name" || { echo "TAMPER_FAIL $name"; exit 11; }
      echo "COLLECTED $name"
    done
    echo ALL_DONE
  ' bash "${specs[@]}"
  status=$?
  if [ "$status" -eq 0 ]; then echo "ALL_COLLECTED $(date +%H:%M:%S)"; exit 0; fi
  sleep 25
done
echo "GAVE_UP"
exit 1
