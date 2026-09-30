#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
exec "$MIGRATION_NODE" "$MIGRATION_PNPM" "$@"
