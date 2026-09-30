#!/usr/bin/env bash
# 旁路预演：共享工程 test-compile 被他人改动打断时，用旁路执行器走一遍标准 bundle 比较。
# 正式采集仍走 capture-keys-small-local.py（Java 执行真实 clean test）；本入口的产物只落在
# .cache/tmp 下，不写 full-evidence-locals.json。TS 侧重新跑真实 Jest 探针。
set -euo pipefail
TASK="$(cd "$(dirname "$0")" && pwd)"
source "$TASK/env.sh"
cd "$TASK"
RUN_INPUT="${1:?用法: rehearse-keys-small.sh <空运行目录>}"
RUN="$TASK/${RUN_INPUT#./}"
SDK="$MIGRATION_UPSTREAM/packages/sdk"
PLAN_ROOT="$TASK/.cache/evidence"
if [ -e "$RUN" ] && [ -n "$(ls -A "$RUN")" ]; then echo "运行目录必须为空：$RUN" >&2; exit 2; fi
STAGE="$RUN/stage"
mkdir -p "$STAGE/ts" "$STAGE/java" "$RUN/ts" "$RUN/java"

CATALOG="$PLAN_ROOT/ecdsa-additional-plan-20260930/catalog.json"
MAPPING="$PLAN_ROOT/ecdsa-additional-plan-20260930/mapping.json"
PLAN="$PLAN_ROOT/ecdsa-additional-plan-20260930/input-plan.json"

# —— TS 侧：真实 Jest 探针，产出本轮 ts-calls 轨迹 ——
for spec in \
  "ecdsa-additional:ECDSA.additional.test.ts:MIGRATION_ECDSA_ADDITIONAL_TS_OBSERVATIONS" \
  "ecdh:ECDH.test.ts:MIGRATION_ECDH_TS_OBSERVATIONS" \
  "secp256r1:Secp256r1.test.ts:MIGRATION_SECP256R1_TS_OBSERVATIONS" \
  "bug-31:bug-31.test.ts:MIGRATION_BUG_31_TS_OBSERVATIONS"; do
  name="${spec%%:*}"; rest="${spec#*:}"; file="${rest%%:*}"; probe_env="${rest##*:}"
  out="$STAGE/ts/$name"; mkdir -p "$out"
  env "$probe_env=$out/calls.raw.jsonl" \
      MIGRATION_PARITY_TS_OBSERVATIONS="$out/assertions.raw.jsonl" \
      MIGRATION_NETWORK_LOG="$out/network.jsonl" \
      "$TASK/pnpm.sh" --dir "$SDK" exec jest --runInBand --watchman=false \
        --runTestsByPath "src/primitives/__tests/$file" \
        --setupFilesAfterEnv "$TASK/ts-offline-guard.cjs" "$TASK/capture-$name-inputs.cjs" \
        "$TASK/capture-parity.cjs" --json --outputFile="$out/jest.json" > "$out/jest.log" 2>&1
  [ -s "$out/network.jsonl" ] && { echo "TS 出现网络调用：$name" >&2; exit 1; }
done

# —— TS 侧 capture：本轮探针轨迹转成 ts 输入与断言 ——
cat > "$STAGE/ts-capture.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
python3 "$TASK/.cache/tmp/keys-small-runner/merge-jest.py" "$STAGE/ts" > "$RUN/ts/ts-jest.json"
: > "\$EVIDENCE_INPUTS_PATH"
: > "\$EVIDENCE_ASSERTIONS_PATH"
for name in ecdsa-additional ecdh secp256r1 bug-31; do
  out="$STAGE/ts/\$name"
  EVIDENCE_RUN_ID="\$EVIDENCE_RUN_ID" python3 "$TASK/prepare-keys-small-local.py" emit-ts \\
    --local "\$name" --raw "\$out/calls.raw.jsonl" \\
    --plan "$PLAN_ROOT/\$name-plan-20260930/input-plan.json" \\
    --output "\$out/inputs.jsonl"
  cat "\$out/inputs.jsonl" >> "\$EVIDENCE_INPUTS_PATH"
  python3 "$TASK/emit-assertion-observations.py" \
    --catalog "$PLAN_ROOT/\$name-plan-20260930/catalog.json" \
    --mapping "$PLAN_ROOT/\$name-plan-20260930/mapping.json" \
    --plan "$PLAN_ROOT/\$name-plan-20260930/input-plan.json" \
    --side ts --raw "\$out/assertions.raw.jsonl" --run-id "\$EVIDENCE_RUN_ID" \
    --output "\$out/assertions.jsonl" --allow-ts-extra
  cat "\$out/assertions.jsonl" >> "\$EVIDENCE_ASSERTIONS_PATH"
done
EOF
chmod +x "$STAGE/ts-capture.sh"

python3 "$TASK/evidence-bundle.py" capture --side ts \
  --catalog "$CATALOG" --mapping "$MAPPING" --input-plan "$PLAN" \
  --inputs "$RUN/ts/inputs.jsonl" --assertions "$RUN/ts/assertions.jsonl" \
  --output "$RUN/ts/run.json" --report "$RUN/ts/ts-jest.json" -- \
  "$STAGE/ts-capture.sh"

# —— Java 侧：bundle 传入 clean/test 两个阶段名，包装器转成旁路执行器 ——
cat > "$STAGE/java-capture.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
[ "\${1:-}" = clean ] && [ "\${2:-}" = test ] || { echo "必须是 clean test" >&2; exit 2; }
MIGRATION_KEYS_SMALL_TASK="$TASK" "$TASK/.cache/tmp/keys-small-runner/keys-small-runner.sh" "$RUN/java" "$RUN/ts/inputs.jsonl"
EOF
chmod +x "$STAGE/java-capture.sh"

python3 "$TASK/evidence-bundle.py" capture --side java \
  --catalog "$CATALOG" --mapping "$MAPPING" --input-plan "$PLAN" \
  --inputs "$RUN/java/inputs.jsonl" --assertions "$RUN/java/assertions.jsonl" \
  --output "$RUN/java/run.json" --report "$RUN/java/java-surefire.xml" -- \
  "$STAGE/java-capture.sh" clean test

python3 "$TASK/evidence-bundle.py" \
  --catalog "$CATALOG" --mapping "$MAPPING" --input-plan "$PLAN" \
  --ts-inputs "$RUN/ts/inputs.jsonl" --java-inputs "$RUN/java/inputs.jsonl" \
  --ts-assertions "$RUN/ts/assertions.jsonl" --java-assertions "$RUN/java/assertions.jsonl" \
  --output "$RUN/parity.json" \
  --ts-run-manifest "$RUN/ts/run.json" --java-run-manifest "$RUN/java/run.json" \
  --ts-report "$RUN/ts/ts-jest.json" --java-report "$RUN/java/java-surefire.xml"
echo "预演完成：$RUN/parity.json"
