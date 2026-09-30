#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
exec "$MIGRATION_MVN" -s "$MIGRATION_SETTINGS" -B \
  "-Dmaven.repo.local=$MIGRATION_ROOT/.cache/maven" "$@"
