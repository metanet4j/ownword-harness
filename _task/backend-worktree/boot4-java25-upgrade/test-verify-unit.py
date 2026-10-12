#!/usr/bin/env python3
"""从通过的真实证据构造反例，验证严格 CLI 不接受缺失、跳过或漂移的报告。"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--evidence", type=Path, required=True)
args = parser.parse_args()
evidence = args.evidence.resolve()
relative = Path("metanet4j-sdk/metanet4j-sdk/unit")


def verify(path):
    return subprocess.run(["python3", str(ROOT / "verify-unit.py"), "--mode", "accept",
                           "--scope", "metanet4j-sdk", "--evidence", str(path)],
                          cwd=ROOT, capture_output=True, text=True)


positive = verify(evidence)
assert positive.returncode == 0, positive.stdout + positive.stderr
cases = ("exec", "jacoco", "surefire", "zero", "skipped", "failures", "errors", "class", "method",
         "sdk", "parent", "command", "during-run-source", "during-run-head")
for case in cases:
    with tempfile.TemporaryDirectory(prefix="ownword-unit-probe-") as temporary:
        probe = Path(temporary)
        output = probe / relative
        shutil.copytree(evidence / relative, output)
        reports = output / "surefire-reports"
        if case == "exec":
            (output / "jacoco-unit.exec").unlink()
            expected = "缺少 JaCoCo 执行数据"
        elif case == "jacoco":
            (output / "jacoco-unit/jacoco.xml").unlink()
            expected = "缺少 JaCoCo XML"
        elif case == "surefire":
            shutil.rmtree(reports)
            expected = "缺少 Surefire XML"
        elif case in ("zero", "skipped", "failures", "errors", "method"):
            for path in reports.glob("TEST-*.xml"):
                tree = ElementTree.parse(path)
                suite = tree.getroot()
                if case == "zero":
                    suite.set("tests", "0")
                    for item in list(suite.findall("testcase")):
                        suite.remove(item)
                elif case == "skipped":
                    suite.set("skipped", "1")
                elif case in ("failures", "errors"):
                    suite.set(case, "1")
                else:
                    for item in suite.findall("testcase"):
                        item.set("name", "undeclaredProbeCase")
                tree.write(path)
            expected = {"zero": "零测试执行", "skipped": "跳过", "method": "用例未发现",
                        "failures": "测试失败或错误", "errors": "测试失败或错误"}[case]
        elif case == "class":
            path = output / "jacoco-unit/jacoco.xml"
            tree = ElementTree.parse(path)
            for package in tree.getroot().findall("package"):
                for item in list(package.findall("class")):
                    package.remove(item)
            tree.write(path)
            expected = "生产类缺失"
        else:
            path = output / "metadata.json"
            metadata = json.loads(path.read_text())
            if case == "sdk":
                metadata["sdkArtifact"]["pomSha256"] = "0" * 64
                expected = "SDK POM 指纹"
            elif case == "parent":
                metadata["sourceFingerprint"] = "0" * 64
                expected = "证据与当前源码不一致"
            elif case == "command":
                metadata["command"].remove("test")
                metadata["command"].append("test-compile")
                expected = "命令未包含 clean test"
            elif case == "during-run-source":
                metadata["invocation"]["startFingerprints"]["metanet4j-sdk"] = "0" * 64
                expected = "执行前后源码或测试资源发生变化"
            else:
                metadata["invocation"]["startHead"] = "0" * 40
                expected = "执行前后提交发生变化"
            path.write_text(json.dumps(metadata))
        result = verify(probe)
        assert result.returncode != 0 and expected in result.stdout, (case, result.stdout, result.stderr)
        print(f"{case}: PASS，反例退出 {result.returncode}")
print(f"严格验收 CLI：真实证据通过，{len(cases)} 类反例全部拒绝")
