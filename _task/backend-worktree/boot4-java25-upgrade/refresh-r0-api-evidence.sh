#!/usr/bin/env bash
# 证据刷新：重跑产物生成与独立复核，并把产物指纹同步进证据，保证「证据 - 产物」自洽。
# 只重算指纹与检查，不改变任何结论；产物若有实质变化，复核与审计会重新判定。
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

python3 evidence/bsv-replace/r0-api-work/build-api-resolution.py
python3 evidence/bsv-replace/r0-api-work/build-api-map.py
python3 evidence/bsv-replace/r0-api-work/verify-api-map.py
python3 bsv-api-audit.py check --json > evidence/bsv-replace/r0-api-work/api-audit.json
python3 evidence/bsv-replace/r0-api-work/build-test-map.py
python3 bsv-api-audit.py test-map --json > evidence/bsv-replace/r0-api-work/test-map-audit.json
python3 evidence/bsv-replace/r0-api-work/check-vectors.py
python3 evidence/bsv-replace/r0-api-work/build-vectors.py
python3 evidence/bsv-replace/r0-api-work/verify-vectors.py

python3 evidence/bsv-replace/r0-api-work/sync-evidence-fingerprints.py
