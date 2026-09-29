#!/usr/bin/env bash
# 一次 Jest 运行采集 6 个 keys 局部的原始入口/断言轨迹，供冻结计划使用。
# 用法：./probe-keys-all.sh <相对运行目录>
set -euo pipefail
TASK="$(cd "$(dirname "$0")" && pwd)"
out="$TASK/$1"
mkdir -p "$out"
SDK="$TASK/../../../reference/ts-stack/packages/sdk"
env MIGRATION_PARITY_TS_OBSERVATIONS="$out/assertions.all.jsonl" \
    MIGRATION_PUBLIC_KEY_TS_OBSERVATIONS="$out/public-key.calls.raw.jsonl" \
    MIGRATION_PUBLIC_KEY_ADDITIONAL_TS_OBSERVATIONS="$out/public-key-additional.calls.raw.jsonl" \
    MIGRATION_ECDSA_TS_OBSERVATIONS="$out/ecdsa.calls.raw.jsonl" \
    MIGRATION_SCHNORR_TS_OBSERVATIONS="$out/schnorr.calls.raw.jsonl" \
    MIGRATION_SYMMETRIC_KEY_TS_OBSERVATIONS="$out/symmetric-key.calls.raw.jsonl" \
    MIGRATION_ECIES_TS_OBSERVATIONS="$out/ecies.calls.raw.jsonl" \
    MIGRATION_NETWORK_LOG="$out/ts-network.jsonl" \
    "$TASK/lock.sh" "$TASK/pnpm.sh" --dir "$SDK" exec jest --runInBand --watchman=false \
    --runTestsByPath \
    src/primitives/__tests/PublicKey.test.ts \
    src/primitives/__tests/PublicKey.additional.test.ts \
    src/primitives/__tests/ECDSA.test.ts \
    src/primitives/__tests/Schnorr.test.ts \
    src/primitives/__tests/SymmetricKey.test.ts \
    src/compat/__tests/ECIES.test.ts \
    --setupFilesAfterEnv \
    "$TASK/ts-offline-guard.cjs" \
    "$TASK/capture-public-key-inputs.cjs" \
    "$TASK/capture-public-key-additional-inputs.cjs" \
    "$TASK/capture-ecdsa-inputs.cjs" \
    "$TASK/capture-schnorr-inputs.cjs" \
    "$TASK/capture-symmetric-key-inputs.cjs" \
    "$TASK/capture-ecies-inputs.cjs" \
    "$TASK/capture-parity.cjs" \
    --json --outputFile="$out/jest.json"
if [ -s "$out/ts-network.jsonl" ]; then
  echo "固定原测试出现网络调用" >&2
  exit 1
fi
python3 - "$out" <<'PY'
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
locals_ = {
    'src/primitives/__tests/PublicKey.test.ts': 'public-key',
    'src/primitives/__tests/PublicKey.additional.test.ts': 'public-key-additional',
    'src/primitives/__tests/ECDSA.test.ts': 'ecdsa',
    'src/primitives/__tests/Schnorr.test.ts': 'schnorr',
    'src/primitives/__tests/SymmetricKey.test.ts': 'symmetric-key',
    'src/compat/__tests/ECIES.test.ts': 'ecies',
}
groups = {name: [] for name in locals_.values()}
for line in (out / 'assertions.all.jsonl').read_text().splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    matches = [name for path, name in locals_.items() if row['file'].endswith(path)]
    if len(matches) != 1:
        raise SystemExit('断言轨迹文件不在冻结范围：' + row['file'])
    groups[matches[0]].append(line)
for name, rows in groups.items():
    (out / f'{name}.assertions.raw.jsonl').write_text(''.join(row + '\n' for row in rows))
    calls = out / f'{name}.calls.raw.jsonl'
    print(name, 'calls', len(calls.read_text().splitlines()) if calls.exists() else 0,
          'assertions', len(rows))
PY
