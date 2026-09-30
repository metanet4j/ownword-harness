#!/usr/bin/env bash
# 冻结前的探针自采：只跑固定原文件，产出 raw 轨迹供 prepare-spend-local.py freeze 使用。
set -euo pipefail
TASK=/home/haodev/ownword/_task/backend-worktree/bsv-sdk-java-migration
SDK=/home/haodev/ownword/reference/ts-stack/packages/sdk
LOCAL="$1"; DIR="$2"; FILE="$3"; PROBE="$4"; OBS_ENV="$5"
cd "$TASK"
mkdir -p "$DIR"
env EVIDENCE_INPUT_PLAN="$DIR/input-plan.json" \
    EVIDENCE_RUN_ID=bootstrap EVIDENCE_SIDE=ts \
    "$OBS_ENV=$DIR/ts-calls.raw.jsonl" \
    MIGRATION_PARITY_TS_OBSERVATIONS="$DIR/ts-assertions.raw.jsonl" \
    MIGRATION_NETWORK_LOG="$DIR/ts-network.jsonl" \
    ./pnpm.sh --dir "$SDK" exec jest --runInBand --watchman=false \
      --runTestsByPath "$FILE" --setupFilesAfterEnv \
      "$TASK/ts-offline-guard.cjs" "$TASK/spend-seeded-entropy.cjs" \
      "$TASK/$PROBE" "$TASK/capture-parity.cjs" \
      --json --outputFile="$DIR/ts-jest.json"
