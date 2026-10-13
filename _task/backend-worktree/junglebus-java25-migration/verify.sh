#!/usr/bin/env bash
set -euo pipefail
task_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd -- "$task_root"
case "${1:-test}" in
  baseline) node baseline.cjs ;;
  test) ./mvn.sh clean test ;;
  package) ./mvn.sh clean verify ;;
  *) printf '用法：./verify.sh baseline|test|package\n' >&2; exit 2 ;;
esac
