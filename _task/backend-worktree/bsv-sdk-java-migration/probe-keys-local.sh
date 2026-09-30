#!/usr/bin/env bash
# 只为冻结计划运行一次 TS 探针：把原始入口/断言轨迹写进给定目录。
# 用法：./probe-keys-local.sh <局部名> <相对运行目录>
set -euo pipefail
TASK="$(cd "$(dirname "$0")" && pwd)"
name="$1"
out="$TASK/$2"
mkdir -p "$out"
read -r FILE ENV_NAME < <(python3 - "$TASK" "$name" <<'PY'
import importlib.util, sys
task, name = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location('keys_locals', task + '/keys-locals.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
entry = module.local(name)
print(entry['file'], entry['ts_observations_env'])
PY
)
SDK="$TASK/../../../reference/ts-stack/packages/sdk"
env "$ENV_NAME=$out/calls.raw.jsonl" \
    MIGRATION_PARITY_TS_OBSERVATIONS="$out/assertions.raw.jsonl" \
    MIGRATION_NETWORK_LOG="$out/ts-network.jsonl" \
    "$TASK/lock.sh" "$TASK/pnpm.sh" --dir "$SDK" exec jest --runInBand --watchman=false \
    --runTestsByPath "$FILE" \
    --setupFilesAfterEnv "$TASK/ts-offline-guard.cjs" "$TASK/capture-$name-inputs.cjs" "$TASK/capture-parity.cjs" \
    --json --outputFile="$out/jest.json"
if [ -s "$out/ts-network.jsonl" ]; then
  echo "固定原测试出现网络调用" >&2
  exit 1
fi
wc -l "$out/calls.raw.jsonl" "$out/assertions.raw.jsonl"
