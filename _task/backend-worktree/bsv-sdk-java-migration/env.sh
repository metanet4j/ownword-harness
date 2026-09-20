#!/usr/bin/env bash
# 只影响当前任务进程；工具路径与版本统一读取 workspace.json。
MIGRATION_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATION_WORKSPACE="$(cd "$MIGRATION_ROOT/../../.." && pwd)"
MIGRATION_CONFIG="$(python3 - "$MIGRATION_ROOT/workspace.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
for key in ('javaHome', 'maven', 'mavenSettings', 'node'):
    print(d['tools'][key])
print(d['upstream']['path'])
PY
)" || return 1
mapfile -t MIGRATION_VALUES <<< "$MIGRATION_CONFIG"
export JAVA_HOME="${MIGRATION_VALUES[0]}"
MIGRATION_MVN="${MIGRATION_VALUES[1]}"
MIGRATION_SETTINGS="${MIGRATION_VALUES[2]}"
MIGRATION_NODE="${MIGRATION_VALUES[3]}"
MIGRATION_UPSTREAM="$MIGRATION_WORKSPACE/${MIGRATION_VALUES[4]}"
MIGRATION_PNPM="$MIGRATION_ROOT/.cache/tools/pnpm/node_modules/pnpm/bin/pnpm.cjs"
export PATH="$MIGRATION_ROOT/.cache/tools/pnpm/node_modules/.bin:$(dirname "$MIGRATION_NODE"):$JAVA_HOME/bin:$PATH"
export npm_config_cache="$MIGRATION_ROOT/.cache/npm"
export npm_config_store_dir="$MIGRATION_ROOT/.cache/pnpm-store"
export XDG_CACHE_HOME="$MIGRATION_ROOT/.cache/xdg"
export PNPM_HOME="$MIGRATION_ROOT/.cache/pnpm-home"
