#!/usr/bin/env python3
"""用真实集成证据验证完整类／实例、失败结果和来源漂移均不能被验收。"""
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
metadata = json.loads((evidence / "metadata.json").read_text())


def verify(path):
    command = ["python3", str(ROOT / "verify-integration.py"), "--scope", metadata["scope"], "--evidence", str(path)]
    if metadata.get("testsFilter"):
        command += ["--tests", metadata["testsFilter"]]
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True)


positive = verify(evidence)
assert positive.returncode == 0, positive.stdout + positive.stderr
for case in ("class", "instances", "skipped", "source"):
    with tempfile.TemporaryDirectory(prefix="ownword-integration-probe-") as temporary:
        probe = Path(temporary) / "evidence"
        shutil.copytree(evidence, probe)
        report = next(probe.glob("*/surefire-reports/TEST-*.xml"))
        if case == "class":
            report.unlink()
            expected = "集成类集合不一致"
        elif case in ("instances", "skipped"):
            tree = ElementTree.parse(report)
            if case == "instances":
                tree.getroot().remove(tree.getroot().find("testcase"))
                expected = "参数化／继承实例计数不符"
            else:
                tree.getroot().set("skipped", "1")
                expected = "用例失败、错误或跳过"
            tree.write(report)
        else:
            path = probe / "metadata.json"
            data = json.loads(path.read_text())
            data["head"] = "0" * 40
            path.write_text(json.dumps(data))
            expected = "证据与当前提交、源码或测试资源不一致"
        result = verify(probe)
        assert result.returncode != 0 and expected in result.stdout, (case, result.stdout, result.stderr)
        print(f"{case}: PASS，反例退出 {result.returncode}")
print("集成验收 CLI：真实证据通过，4 类反例全部拒绝")
