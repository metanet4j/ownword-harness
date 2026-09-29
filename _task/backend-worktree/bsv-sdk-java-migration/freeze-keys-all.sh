#!/usr/bin/env bash
# 从一次探针运行的原始轨迹冻结 6 个 keys 局部的清单/映射/输入计划。
# 用法：./freeze-keys-all.sh <探针运行目录> <计划日期后缀>
set -euo pipefail
TASK="$(cd "$(dirname "$0")" && pwd)"
run="$TASK/$1"
suffix="$2"
for name in public-key public-key-additional ecdsa schnorr symmetric-key ecies; do
  python3 "$TASK/prepare-keys-local.py" freeze --local "$name" \
    --raw "$run/$name.calls.raw.jsonl" \
    --assertions "$run/$name.assertions.raw.jsonl" \
    --directory "$TASK/.cache/evidence/$name-plan-$suffix"
done
