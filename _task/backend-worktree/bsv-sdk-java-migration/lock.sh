#!/usr/bin/env bash
# 串行化共享目标工程的 Maven／采集运行。多代理并行时，任何会写 metanet4j-bsv-sdk/target
# 或改动 full-evidence-locals.json 的命令都要走这里：./lock.sh <命令...>
set -euo pipefail
TASK="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$TASK/.cache"
exec flock "$TASK/.cache/run.lock" "$@"
