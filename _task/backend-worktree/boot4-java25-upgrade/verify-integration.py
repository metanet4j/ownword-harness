#!/usr/bin/env python3
"""独立保存并验收集成报告、逐类／方法清单、源码指纹及本轮资源清理。"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("unit", ROOT / "verify-unit.py")
unit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(unit)


def command_output(command):
    result = subprocess.run(command, text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError(result.stderr[-1000:])
    return result.stdout.strip()


def residuals(resources):
    """只查询本轮登记名字；不执行任何删除命令。"""
    result = {}
    mongo = sorted(resources.get("mongo", []))
    if mongo:
        query = "print(JSON.stringify(db.adminCommand({listDatabases:1,nameOnly:true,filter:{name:{$in:"
        query += json.dumps(mongo) + "}}}).databases.map(x=>x.name)))"
        result["mongo"] = json.loads(command_output(["docker", "exec", "infra-mongo", "mongosh",
                "--username", "bschema", "--password", "bschema123", "--authenticationDatabase", "admin",
                "--quiet", "--eval", query]))
    mysql = sorted(resources.get("mysql", []))
    if mysql:
        assert all(re.fullmatch(r"it_[a-z0-9_]+", name) for name in mysql)
        query = "select schema_name from information_schema.schemata where schema_name in ("
        query += ",".join("'" + name + "'" for name in mysql) + ")"
        value = command_output(["docker", "exec", "infra-mysql", "mysql", "-uroot", "-proot123",
                                "--batch", "--skip-column-names", "-e", query])
        result["mysql"] = value.splitlines() if value else []
        result["mysql-table"] = [name for name in resources.get("mysql-table", [])
                                  if name.split(".", 1)[0] in result["mysql"]]
    if resources.get("es"):
        with urlopen("http://localhost:9200/_cat/indices?format=json&h=index", timeout=30) as response:
            names = {item["index"] for item in json.load(response)}
        result["es"] = sorted(names.intersection(resources["es"]))
    for kind, executable in [("kafka-topic", "kafka-topics.sh"), ("kafka-group", "kafka-consumer-groups.sh")]:
        if resources.get(kind):
            names = set(command_output(["docker", "exec", "infra-kafka", "/opt/kafka/bin/" + executable,
                    "--bootstrap-server", "localhost:9092", "--list"]).splitlines())
            result[kind] = sorted(names.intersection(resources[kind]))
    if resources.get("redis-prefix"):
        left = []
        for prefix in resources["redis-prefix"]:
            value = command_output(["docker", "exec", "infra-redis", "redis-cli", "--scan", "--pattern", prefix + "*"])
            if value:
                left.extend(value.splitlines())
        result["redis-prefix"] = left
    result["temp-dir"] = [name for name in resources.get("temp-dir", []) if Path(name).exists()]
    left_ports = []
    for name in resources.get("tcp-port", []):
        with socket.socket() as probe:
            probe.settimeout(2)
            if probe.connect_ex(("127.0.0.1", int(name))) == 0:
                left_ports.append(name)
    result["tcp-port"] = left_ports
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("component", "http"), required=True)
    parser.add_argument("--tests", help="仅用于阶段验证；最终验收不得限制测试类")
    parser.add_argument("--evidence", type=Path, help="核对已有证据，不重跑 Maven")
    args = parser.parse_args()
    repository = "metanet4j-component" if args.scope == "component" else "metanet4j-sdk"
    repo = next(item for item in unit.inventory() if item["repository"] == repository)
    modules = repo["modules"]
    frozen = json.loads((ROOT / "bsv-replace-test-map.json").read_text())["integrationSets"]
    if args.scope == "component":
        expected = frozen["componentIntegration"]["classes"]
    else:
        entry = frozen["sdkLocalHttp"]
        expected = [{"class": "com.metanet4j.sdk.utxo." + entry["class"],
                     "module": "metanet4j-sdk", "executedTests": entry["expectedCases"]}]
    if args.tests:
        names = set(args.tests.split(","))
        expected = [item for item in expected if item["class"] in names or item["class"].split(".")[-1] in names]
        if len(expected) != len(names):
            raise ValueError("指定类不在完整集成清单内")
    fingerprints = {item["artifactId"]: unit.fingerprint(repository, item) for item in modules}
    head = command_output(["git", "-C", str(ROOT / repository), "rev-parse", "HEAD"])
    if args.evidence:
        evidence = args.evidence.resolve()
        metadata = json.loads((evidence / "metadata.json").read_text())
    else:
        evidence = ROOT / "evidence" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + args.scope + "-integration")
        evidence.mkdir(parents=True)
        command = [str(unit.MVN), "-s", str(unit.SETTINGS), "-B", "clean", "test",
                   "-Dgroups=integration", "-DexcludedGroups=external"]
        if args.tests:
            command += ["-Dtest=" + args.tests, "-Dsurefire.failIfNoSpecifiedTests=false"]
        started = datetime.now(timezone.utc).timestamp()
        environment = os.environ.copy()
        environment["JAVA_HOME"] = str(unit.JDK)
        with (evidence / "maven.log").open("w") as log:
            run = subprocess.run(command, cwd=ROOT / repository, env=environment, stdout=log, stderr=subprocess.STDOUT)
        for module in modules:
            directory = ROOT / repository / module["path"] / "target/surefire-reports"
            for report in directory.glob("*"):
                if report.is_file() and report.stat().st_mtime >= started:
                    target = evidence / module["artifactId"] / "surefire-reports"
                    target.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(report, target / report.name)
        metadata = {"scope": args.scope, "repository": repository, "head": head, "command": command,
                    "testsFilter": args.tests, "startedAt": started, "exitCode": run.returncode,
                    "sourceFingerprints": fingerprints, "sdkArtifact": unit.sdk_artifact()}
        (evidence / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    problems = []
    if metadata.get("exitCode") != 0:
        problems.append("Maven 退出码非零")
    if metadata.get("head") != head or metadata.get("sourceFingerprints") != fingerprints:
        problems.append("证据与当前提交、源码或测试资源不一致")
    if metadata.get("testsFilter") != args.tests:
        problems.append("证据的集成范围不一致")
    if metadata.get("sdkArtifact") != unit.sdk_artifact():
        problems.append("固定 SDK 制品指纹不一致")
    artifact = unit.sdk_artifact()
    expected_sdk = unit.sdk_manifest()
    if artifact.get("jarSha256") != expected_sdk.get("installedJarSha256") or artifact.get("pomSha256") != expected_sdk.get("installedPomSha256"):
        problems.append("SDK 制品与固定来源清单不一致")
    if any(token not in metadata.get("command", []) for token in
           ("clean", "test", "-Dgroups=integration", "-DexcludedGroups=external")):
        problems.append("集成命令不符合要求")
    cases = {}
    module_counts = {}
    for report in sorted(evidence.glob("*/surefire-reports/TEST-*.xml")):
        suite = ElementTree.parse(report).getroot()
        module = report.parent.parent.name
        count = module_counts.setdefault(module, dict(tests=0, failures=0, errors=0, skipped=0))
        for key in count:
            count[key] += int(suite.get(key, "0"))
        if any(int(suite.get(key, "0")) for key in ("failures", "errors", "skipped")):
            problems.append("用例失败、错误或跳过：" + str(suite.get("name")))
        cases.setdefault(suite.get("name"), []).extend(suite.findall("testcase"))
    expected_names = {item["class"] for item in expected}
    if set(cases) != expected_names:
        problems.append("集成类集合不一致：缺少 " + str(sorted(expected_names - set(cases)))
                        + "；多出 " + str(sorted(set(cases) - expected_names)))
    class_summary = []
    for item in expected:
        actual = cases.get(item["class"], [])
        if len(actual) != item["executedTests"]:
            problems.append("参数化／继承实例计数不符：" + item["class"])
        relative = item["class"].replace(".", "/") + ".java"
        source = next((source for module in modules for source in module["testSources"]
                       if source["path"].endswith("src/test/java/" + relative)), None)
        if source is None:
            problems.append("测试源码未登记：" + item["class"])
        else:
            names = [case.get("name", "") for case in actual]
            for method in source["methods"]:
                if method["classification"] == "integration" and not any(
                        name == method["name"] or name.startswith(method["name"] + "(") for name in names):
                    problems.append("集成方法未执行：" + item["class"] + "#" + method["name"])
        class_summary.append({"class": item["class"], "cases": [case.get("name") for case in actual]})
    resources = {}
    for kind, name in re.findall(r"^OWNWORD_TEST_RESOURCE (\S+) (\S+)\s*$",
                                (evidence / "maven.log").read_text(), re.M):
        resources.setdefault(kind, set()).add(name)
    resources = {kind: sorted(names) for kind, names in resources.items()}
    if args.scope == "component":
        try:
            left = residuals(resources)
            if any(left.values()):
                problems.append("本轮资源有残留")
        except Exception as failure:
            left = {"checkError": str(failure)}
            problems.append("本轮资源检查失败")
        if not args.tests and not {"mongo", "mysql", "mysql-table", "es", "redis-prefix", "kafka-topic", "kafka-group"}.issubset(resources):
            problems.append("完整集成资源登记不齐")
    else:
        left = {}
    summary = {"scope": args.scope, "full": not args.tests, "moduleCounts": module_counts,
               "classes": class_summary, "resources": resources, "residuals": left, "problems": problems,
               "formalAcceptance": not problems}
    (evidence / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"modules": module_counts, "classes": len(cases), "problems": problems,
                      "resources": {kind: len(names) for kind, names in resources.items()}, "residuals": left}, ensure_ascii=False))
    print("证据：" + str(evidence))
    return int(bool(problems))


if __name__ == "__main__":
    sys.exit(main())
