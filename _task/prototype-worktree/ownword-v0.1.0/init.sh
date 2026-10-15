#!/usr/bin/env bash
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$TASK_DIR/ownword-prototype"
node ../verify-environment.cjs
if [[ "${1:---check}" == '--serve' ]]; then
  exec python3 -u -m http.server 4311 --bind 127.0.0.1
fi
