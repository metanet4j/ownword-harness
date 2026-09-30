#!/usr/bin/env python3
"""用真实证据的篡改副本验证 Symmetric manual 核验器会拒绝缺失和伪通过。"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / '.cache/evidence'
VERIFY = ROOT / 'verify-symmetric-manual.py'


def run(output, *args, success):
    process = subprocess.run([sys.executable, str(VERIFY), '--output', str(output), *map(str, args)],
                             capture_output=True, text=True)
    assert (process.returncode == 0) == success, process.stdout + process.stderr


def main():
    with tempfile.TemporaryDirectory() as dirname:
        temp = Path(dirname)
        report = temp / 'report.json'
        run(report, success=True)
        assert json.loads(report.read_text())['assertionsCompared'] == 387

        missing = temp / 'missing.json'
        run(report, '--java-summary', missing, success=False)

        observations = temp / 'ts.jsonl'
        items = [json.loads(line) for line in (EVIDENCE / 'symmetric-manual-ts-retry-20260926.jsonl').read_text().splitlines()]
        items[1]['actualLength'] -= 1
        observations.write_text(''.join(json.dumps(item) + '\n' for item in items))
        run(report, '--ts-observations', observations, success=False)

        summary = temp / 'java.json'
        item = json.loads((EVIDENCE / 'symmetric-manual-java-current-c0d9fdd.json').read_text())
        item['bytewiseCompared'] -= 1
        summary.write_text(json.dumps(item))
        original = (EVIDENCE / 'symmetric-manual-java-current-c0d9fdd-surefire.xml').read_text()
        linked_xml = temp / 'linked-surefire.xml'
        linked_xml.write_text(original.replace(str(EVIDENCE / 'symmetric-manual-java-current-c0d9fdd.json'),
                                               str(summary)))
        run(report, '--java-summary', summary, '--java-xml', linked_xml, success=False)

        xml = temp / 'surefire.xml'
        xml.write_text(original.replace('tests="1"', 'tests="0"', 1))
        run(report, '--java-xml', xml, success=False)

        normal = temp / 'normal.jsonl'
        lines = (EVIDENCE / 'symmetric-java-parity-current-c0d9fdd.jsonl').read_text().splitlines()
        first = json.loads(lines[0])
        first['matcher'] = 'tampered'
        lines[0] = json.dumps(first)
        normal.write_text('\n'.join(lines) + '\n')
        xml_dir = temp / 'normal-xml'
        xml_dir.mkdir()
        original_trace = str(EVIDENCE / 'symmetric-java-parity-current-c0d9fdd.jsonl')
        for source in (EVIDENCE / 'symmetric-java-current-c0d9fdd-surefire').glob('TEST-*.xml'):
            (xml_dir / source.name).write_text(source.read_text().replace(original_trace, str(normal)))
        run(report, '--java-normal', normal, '--java-normal-xml-dir', xml_dir, success=False)

        run(report, '--java-revision', '0' * 40, success=False)
    print('7/7：真实证据通过；缺失、TS 长度、Java 逐字节、Surefire、普通轨迹和提交篡改均拒绝')


if __name__ == '__main__':
    main()
