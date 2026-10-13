#!/usr/bin/env python3
"""核对已执行测试、交付 JAR 与真实 100 条交易，保存可审查证据。"""
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

task = Path(__file__).resolve().parent
project = task / 'metanet4j-junglebus'
artifacts = task / 'artifacts'

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

reports = {}
expected = {'ProtocolTest': 7, 'RestTest': 6, 'SubscriptionTest': 8, 'LifecycleTest': 16}
for path in (project / 'target/surefire-reports').glob('TEST-*.xml'):
    root = ET.parse(path).getroot()
    name = root.attrib['name'].rsplit('.', 1)[-1]
    reports[name] = {key: int(root.attrib[key]) for key in ('tests', 'failures', 'errors', 'skipped')}
    assert name in expected and reports[name]['tests'] == expected[name]
    assert not sum(reports[name][key] for key in ('failures', 'errors', 'skipped'))
    reports[name]['cases'] = [case.attrib['name'] for case in root.findall('testcase')]
assert set(reports) == set(expected)

jars = {}
for path in sorted((project / 'target').glob('*.jar')):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        license_name = next((name for name in names if name in ('LICENSE', 'META-INF/LICENSE', 'resources/LICENSE')), None)
        notice_name = next((name for name in names if name in ('NOTICE', 'META-INF/NOTICE', 'resources/NOTICE')), None)
        assert license_name and notice_name, f'{path.name} 缺少许可证'
        assert archive.read(license_name) == (project / 'LICENSE').read_bytes()
        assert archive.read(notice_name) == (project / 'NOTICE').read_bytes()
        if path.name.endswith('-sources.jar'):
            assert 'com/metanet4j/junglebus/JungleBusClient.java' in names
        elif path.name.endswith('-javadoc.jar'):
            assert 'com/metanet4j/junglebus/JungleBusClient.html' in names
        else:
            data = archive.read('com/metanet4j/junglebus/JungleBusClient.class')
            assert int.from_bytes(data[6:8], 'big') == 69
        jars[path.name] = {'bytes': path.stat().st_size, 'sha256': digest(path), 'license': license_name, 'notice': notice_name}
assert len(jars) == 3
save(artifacts / 'java-verification.json', {'tests': reports, 'total': sum(expected.values()), 'classMajorVersion': 69, 'jars': jars})
baseline = json.loads((task / '.cache/evidence/js-baseline.json').read_text())
assert baseline['passed'] and baseline['checks'] == 77
save(artifacts / 'js-baseline.json', baseline)

live = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else artifacts / 'live-json-20261013-123500'
rows = [json.loads(line) for line in (live / 'transactions.jsonl').read_text().splitlines()]
summary = json.loads((live / 'summary.json').read_text())
assert len(rows) == 100 and [row['sequence'] for row in rows] == list(range(1, 101))
assert summary['success'] and summary['received'] == 100 and summary['unsubscribeConfirmed'] and summary['clientState'] == 'CLOSED' and summary['errors'] == 0
for row in rows:
    tx = row['transaction']; raw = bytes.fromhex(tx['transaction'])
    assert raw and re.fullmatch('[0-9a-f]{64}', tx['id'])
    assert hashlib.sha256(hashlib.sha256(raw).digest()).digest()[::-1].hex() == tx['id']
    bytes.fromhex(tx['merkleProof'])
save(live / 'validation.json', {
    'records': len(rows), 'uniqueIds': len({row['transaction']['id'] for row in rows}), 'transactionIdChecks': len(rows),
    'heightMin': min(row['transaction']['blockHeight'] for row in rows), 'heightMax': max(row['transaction']['blockHeight'] for row in rows),
    'sha256': {path.name: digest(path) for path in sorted(live.iterdir()) if path.is_file() and path.name != 'validation.json'}
})
print(f'证据核对通过：Java {sum(expected.values())} 项，JS {baseline["checks"]} 项，3 类 JAR，真实交易 {len(rows)} 条及其交易 ID 校验。')
