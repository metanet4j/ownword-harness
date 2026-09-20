#!/usr/bin/env bash
# 环境验证分项运行；迁移验收还需满足测试迁移契约中的逐项映射。
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
cd "$MIGRATION_ROOT"
mkdir -p .cache/evidence
run_logged() {
  local name="$1"
  shift
  printf '运行 %s\n' "$name"
  if "$@" > ".cache/evidence/$name.log" 2>&1; then
    tail -n 8 ".cache/evidence/$name.log"
  else
    tail -n 40 ".cache/evidence/$name.log"
    return 1
  fi
}
case "${1:-}" in
  java-build)
    run_logged metanet4j-parent-build ./mvn.sh -o -f metanet4j-parent/pom.xml -N install
    for repo in "$MIGRATION_JAVA_TARGET" metanet4j-base metanet4j-sdk metanet4j-component; do
      run_logged "$repo-build" ./mvn.sh -o -f "$repo/pom.xml" clean install -DskipTests
    done
    ;;
  bsv-test|bsv-build)
    run_logged bsv-test ./mvn.sh -o -f "$MIGRATION_JAVA_TARGET/pom.xml" clean test
    python3 - "$MIGRATION_JAVA_TARGET" <<'PY'
from collections import Counter
from pathlib import Path
import json, sys, xml.etree.ElementTree as E
project = Path(sys.argv[1])
cases = []
for report in sorted((project / 'target/surefire-reports').glob('TEST-*.xml')):
    suite = E.parse(report).getroot()
    rows = suite.findall('testcase')
    assert int(suite.attrib['tests']) == len(rows), report
    assert all(int(suite.attrib[key]) == 0 for key in ('failures', 'errors', 'skipped')), report
    cases.extend(rows)
assert cases, '未找到实际执行的用例'
assert all(not any(c.find(tag) is not None for tag in ('failure', 'error', 'skipped')) for c in cases)
assert any(c.attrib['classname'] == 'com.metanet4j.bsv.infrastructure.BuildInfrastructureTest'
           and c.attrib['name'] == 'preservesUtf8FixtureBytes' for c in cases), '基础资源测试未执行'
counts = Counter(c.attrib['classname'].removeprefix('com.metanet4j.bsv.').split('.')[0] for c in cases)
result = {'project': project.name, 'tests': len(cases), 'failures': 0, 'errors': 0, 'skipped': 0,
          'byPackage': dict(sorted(counts.items())),
          'cases': [c.attrib['classname'] + '#' + c.attrib['name'] for c in cases]}
Path('.cache/evidence/bsv-test.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
PY
    if [[ "$1" == bsv-build ]]; then
      # 已完成 clean test；此步仅打包并安装到任务缓存，不重复执行测试。
      run_logged bsv-build ./mvn.sh -o -f "$MIGRATION_JAVA_TARGET/pom.xml" install -DskipTests
    fi
    ;;
  java-smoke)
    run_logged java-smoke ./mvn.sh -o -f metanet4j-sdk/pom.xml clean test -Dtest=BapDataLockBuilderSignTypeTest
    python3 - <<'PY'
from pathlib import Path
import json, xml.etree.ElementTree as E
p = Path('metanet4j-sdk/target/surefire-reports/TEST-com.metanet4j.sdk.transcation.BapDataLockBuilderSignTypeTest.xml')
d = E.parse(p).getroot()
cases = d.findall('testcase')
assert len(cases) == 3, 'SDK 冒烟应实际执行 3 个用例'
assert all(not c.findall('failure') and not c.findall('error') and not c.findall('skipped') for c in cases)
result = {'module': 'metanet4j-sdk', 'tests': len(cases), 'failures': 0, 'errors': 0, 'skipped': 0, 'cases': [c.attrib['name'] for c in cases]}
Path('.cache/evidence/java-smoke.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
PY
    ;;
  ts-build)
    run_logged ts-build ./pnpm.sh --dir "$MIGRATION_UPSTREAM" --filter @bsv/sdk build
    ;;
  ts-smoke)
    # 显式列出已审查为离线算法的测试文件，不自动执行外部接口/钱包测试。
    tests=(
      src/compat/__tests/BSM.test.ts
      src/compat/__tests/ECIES.test.ts
      src/compat/__tests/HD.test.ts
      src/compat/__tests/Mnemonic.test.ts
      src/compat/__tests/Mnemonic.additional.test.ts
      src/primitives/__tests/PrivateKey.test.ts
      src/primitives/__tests/Signature.test.ts
      src/primitives/__tests/TransactionSignature.additional.test.ts
      src/script/templates/__tests/P2PKH.async-backend.test.ts
    )
    run_logged ts-smoke ./pnpm.sh --dir "$MIGRATION_UPSTREAM/packages/sdk" exec jest \
      --runInBand --watchman=false --runTestsByPath "${tests[@]}" \
      --json --outputFile="$MIGRATION_ROOT/.cache/evidence/ts-smoke.json"
    python3 - <<'PY'
from pathlib import Path
import json
d = json.loads(Path('.cache/evidence/ts-smoke.json').read_text())
assert d['success'] and d['numTotalTestSuites'] == 9 and d['numTotalTests'] > 0
assert d['numTotalTests'] == d['numPassedTests']
assert d['numFailedTests'] == d['numPendingTests'] == d['numTodoTests'] == 0
for suite in d['testResults']:
    assert suite['assertionResults'] and all(c['status'] == 'passed' for c in suite['assertionResults'])
    print(Path(suite['name']).name, len(suite['assertionResults']), 'passed')
PY
    ;;
  *) printf '%s\n' '用法：./verify.sh bsv-test|bsv-build|java-build|java-smoke|ts-build|ts-smoke' >&2; exit 2 ;;
esac
