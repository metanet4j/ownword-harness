#!/usr/bin/env bash
# 离线复核 6 个 script 局部的断言轨迹能否按冻结计划映射（不写 target，不跑 Maven）：
# TS 原始断言轨迹由探针采集；Java 原始断言轨迹用自编译类路径单独运行该测试类。
set -uo pipefail
cd "$(dirname "$0")"
CP="/tmp/main-classes:/tmp/probe-classes:$PWD/metanet4j-bsv-sdk/src/test/resources:$(cat /tmp/script-batch-cp.txt):$PWD/.cache/maven/org/junit/platform/junit-platform-launcher/6.0.3/junit-platform-launcher-6.0.3.jar"
JAVA_HOME=$(python3 -c "import json;print(json.load(open('workspace.json'))['tools']['javaHome'])")
OUT=.cache/evidence/offline-check-20260929
mkdir -p "$OUT"
declare -A RAW=( [r-puzzle]=.cache/evidence/r-puzzle-probe-20260929 [p2pkh-async-backend]=.cache/evidence/p2pkh-probe-20260929 [push-drop]=.cache/evidence/push-drop-probe-20260929 [transaction-evidence]=.cache/evidence/transaction-evidence-probe-20260929 [transaction-verifier]=.cache/evidence/transaction-verifier-probe-20260929 [transaction-evidence-coordinator]=.cache/evidence/coordinator-probe2-20260929 )
declare -A PLAN=( [r-puzzle]=.cache/evidence/r-puzzle-plan-20260929 [p2pkh-async-backend]=.cache/evidence/p2pkh-async-backend-plan-20260929 [push-drop]=.cache/evidence/push-drop-plan-20260929 [transaction-evidence]=.cache/evidence/transaction-evidence-plan-20260929 [transaction-verifier]=.cache/evidence/transaction-verifier-plan-20260929 [transaction-evidence-coordinator]=.cache/evidence/transaction-evidence-coordinator-plan-20260929 )
declare -A CLASS=( [r-puzzle]=com.metanet4j.bsv.script.templates.RPuzzleTest [p2pkh-async-backend]=com.metanet4j.bsv.script.templates.P2PKHAsyncBackendTest [push-drop]=com.metanet4j.bsv.script.templates.PushDropTest [transaction-evidence]=com.metanet4j.bsv.transaction.TransactionEvidenceTest [transaction-verifier]=com.metanet4j.bsv.transaction.TransactionVerifierTest [transaction-evidence-coordinator]=com.metanet4j.bsv.transaction.TransactionEvidenceCoordinatorTest )
declare -A INPUT_ENV=( [r-puzzle]=MIGRATION_R_PUZZLE_TS_INPUTS [p2pkh-async-backend]=MIGRATION_P2PKH_ASYNC_BACKEND_TS_INPUTS [push-drop]=MIGRATION_PUSH_DROP_TS_INPUTS [transaction-evidence]=MIGRATION_TRANSACTION_EVIDENCE_TS_INPUTS [transaction-verifier]=MIGRATION_TRANSACTION_VERIFIER_TS_INPUTS [transaction-evidence-coordinator]=MIGRATION_TRANSACTION_EVIDENCE_COORDINATOR_TS_INPUTS )

for local in r-puzzle p2pkh-async-backend push-drop transaction-evidence transaction-verifier transaction-evidence-coordinator; do
  raw="${RAW[$local]}"; plan="${PLAN[$local]}"
  runid=$(python3 -c "import uuid;print(uuid.uuid4().hex)")
  rm -f "$OUT/$local-java-inputs.jsonl" "$OUT/$local-java-assertions.raw.jsonl" \
        "$OUT/$local-java-assertions.jsonl" "$OUT/$local-ts-assertions.jsonl"
  env EVIDENCE_SIDE=java EVIDENCE_RUN_ID="$runid" \
      EVIDENCE_INPUTS_PATH="$PWD/$OUT/$local-java-inputs.jsonl" \
      "${INPUT_ENV[$local]}=$PWD/$raw/ts-inputs.jsonl" \
      "$JAVA_HOME/bin/java" -Dmigration.parity.java.output="$PWD/$OUT/$local-java-assertions.raw.jsonl" \
      -cp "$CP" RunProbe "${CLASS[$local]}" > "$OUT/$local-java.log" 2>&1 || { echo "JAVA_RUN_FAIL $local"; tail -3 "$OUT/$local-java.log"; continue; }
  python3 emit-assertion-observations.py --catalog "$plan/catalog.json" --mapping "$plan/mapping.json" \
      --plan "$plan/input-plan.json" --side java --raw "$OUT/$local-java-assertions.raw.jsonl" \
      --run-id "$runid" --output "$OUT/$local-java-assertions.jsonl" --allow-java-extra \
      || { echo "JAVA_EMIT_FAIL $local"; continue; }
  python3 emit-assertion-observations.py --catalog "$plan/catalog.json" --mapping "$plan/mapping.json" \
      --plan "$plan/input-plan.json" --side ts --raw "$raw/assertions.raw.jsonl" \
      --run-id "$runid" --output "$OUT/$local-ts-assertions.jsonl" --allow-ts-extra \
      || { echo "TS_EMIT_FAIL $local"; continue; }
  python3 - "$local" "$OUT" "$plan" <<'PY'
import importlib.util, json, sys
from pathlib import Path
TASK = Path.cwd()
spec = importlib.util.spec_from_file_location('audit_tests', TASK / 'audit-tests.py')
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
local, out, plan_path = sys.argv[1], sys.argv[2], sys.argv[3]
ts = [json.loads(l) for l in open(f'{out}/{local}-ts-assertions.jsonl')]
java = [json.loads(l) for l in open(f'{out}/{local}-java-assertions.jsonl')]
plan = json.load(open(f'{plan_path}/input-plan.json'))
fails = []
if len(ts) != len(java):
    fails.append(f'条数不同 ts={len(ts)} java={len(java)}')
for left, right in zip(ts, java):
    case, identity = left['caseId'], left['assertionId']
    if identity != right['assertionId']:
        fails.append(f'身份不同 {identity} / {right["assertionId"]}'); continue
    try:
        audit.compare_actuals(case, plan[case], identity, left['value'], right['value'])
    except ValueError as error:
        fails.append(f'{identity.split("__tests/")[-1]} :: {error}')
print(f'{local}: assertions ts={len(ts)} java={len(java)} equal={not fails}')
for line in fails[:3]:
    print('   ', line)
PY
PY
done
echo OFFLINE_CHECK_DONE
