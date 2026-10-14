#!/usr/bin/env bash
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$TASK_DIR/ownword-prototype"
if [[ "${1:-}" == "--serve" ]]; then
  exec python3 -m http.server 4315 --bind 127.0.0.1
fi
npm run check
