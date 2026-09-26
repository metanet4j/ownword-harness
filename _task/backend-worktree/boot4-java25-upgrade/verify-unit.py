#!/usr/bin/env python3
"""按模块运行单元测试并核对 Surefire 与 JaCoCo 证据。"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parent
MVN = Path.home() / ".sdkman/candidates/maven/3.9.16/bin/mvn"
SETTINGS = Path.home() / ".m2/metanet4j-settings.xml"
JDK = Path.home() / ".sdkman/candidates/java/25.0.4.1-tem"
REPOSITORIES = ("metanet4j-parent", "metanet4j-base", "metanet4j-sdk", "metanet4j-component")


def inventory():
    data = json.loads((ROOT / "unit-test-inventory.json").read_text())
    repos = data["repositories"]
    actual_poms = {p.relative_to(ROOT).as_posix() for name in REPOSITORIES
                   for p in (ROOT / name).rglob("pom.xml") if "target" not in p.parts}
    listed_poms = {f"{repo['repository']}/{module['path']}/pom.xml".replace("/./", "/")
                   for repo in repos for module in repo["modules"]}
    if actual_poms != listed_poms or len(actual_poms) != 25:
        raise ValueError(f"POM 清单不一致：缺少 {sorted(actual_poms - listed_poms)}；多列 {sorted(listed_poms - actual_poms)}")
    for repo in repos:
        for module in repo["modules"]:
            directory = ROOT / repo["repository"] / module["path"]
            actual = {p.relative_to(ROOT / repo["repository"]).as_posix()
                      for p in (directory / "src/main/java").rglob("*.java")}
            listed = {item["path"] for item in module["production"]}
            if actual != listed:
                raise ValueError(f"{module['artifactId']} 生产源码清单不一致")
            actual_tests = {p.relative_to(ROOT / repo["repository"]).as_posix()
                            for p in (directory / "src/test/java").rglob("*.java")}
            listed_tests = {item["path"] for item in module["testSources"]}
            if actual_tests != listed_tests:
                raise ValueError(f"{module['artifactId']} 测试源码清单不一致")
    return repos


def select(repos, scope):
    modules = [(repo, module) for repo in repos for module in repo["modules"]]
    if scope == "all":
        return [(repo, module) for repo, module in modules if module["production"]]
    selected = [(repo, module) for repo, module in modules
                if module["artifactId"] == scope or repo["repository"] == scope]
    if not selected:
        raise ValueError(f"未知模块或仓库：{scope}")
    return [(repo, module) for repo, module in selected if module["production"]]


def require_classification(selected):
    incomplete = [module["artifactId"] for _, module in selected
                  if not module.get("classificationReviewed")]
    if incomplete:
        raise ValueError("先完成测试分类，禁止执行自动基线：" + ", ".join(incomplete))


def run_maven(repo_name, args, log_path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = [str(MVN), "-s", str(SETTINGS), "-B", *args]
    environment = os.environ.copy()
    environment["JAVA_HOME"] = str(JDK)
    with log_path.open("w") as log:
        result = subprocess.run(command, cwd=ROOT / repo_name, env=environment,
                                stdout=log, stderr=subprocess.STDOUT, check=False)
    print(f"{repo_name}: exit={result.returncode}，日志 {log_path}", flush=True)
    return result.returncode, command


def fingerprint(repo_name, module):
    digest = hashlib.sha256()
    for source in sorted([*module["production"], *module["testSources"]], key=lambda item: item["path"]):
        path = ROOT / repo_name / source["path"]
        digest.update(source["path"].encode())
        digest.update(path.read_bytes())
    digest.update((ROOT / repo_name / module["path"] / "pom.xml").read_bytes())
    return digest.hexdigest()


def save_artifacts(repo, module, run_root, command, exit_code, log_path):
    target = ROOT / repo["repository"] / module["path"] / "target"
    output = run_root / repo["repository"] / module["artifactId"] / "unit"
    output.mkdir(parents=True, exist_ok=True)
    for source, name in ((target / "surefire-reports", "surefire-reports"),
                         (target / "site/jacoco-unit", "jacoco-unit")):
        if source.exists():
            shutil.copytree(source, output / name, dirs_exist_ok=True)
    if (target / "jacoco-unit.exec").exists():
        shutil.copy2(target / "jacoco-unit.exec", output / "jacoco-unit.exec")
    if log_path.exists():
        shutil.copy2(log_path, output / "maven.log")
    head = subprocess.check_output(["git", "-C", str(ROOT / repo["repository"]),
                                    "rev-parse", "HEAD"], text=True).strip()
    metadata = {"head": head, "command": command, "exitCode": exit_code,
                "artifactId": module["artifactId"], "repository": repo["repository"],
                "sourceFingerprint": fingerprint(repo["repository"], module)}
    (output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    return output


def inspect(module, output, strict):
    problems = []
    metadata_path = output / "metadata.json"
    if not metadata_path.is_file():
        problems.append("缺少运行元数据")
    else:
        metadata = json.loads(metadata_path.read_text())
        if metadata.get("exitCode") != 0:
            problems.append(f"记录的 Maven 退出码非零：{metadata.get('exitCode')}")
        command = metadata.get("command", [])
        command_text = command if isinstance(command, str) else " ".join(command)
        if "clean" not in command_text or "test" not in command_text:
            problems.append("命令未包含 clean test")
        if "-DskipTests" in command_text or "maven.test.skip" in command_text:
            problems.append("命令跳过测试")
        if strict:
            repo_name = metadata.get("repository", "")
            if repo_name not in REPOSITORIES or metadata.get("sourceFingerprint") != fingerprint(repo_name, module):
                problems.append("证据与当前源码不一致")
            elif metadata.get("head") != subprocess.check_output(
                    ["git", "-C", str(ROOT / repo_name), "rev-parse", "HEAD"], text=True).strip():
                problems.append("证据与当前提交不一致")
    reports = sorted((output / "surefire-reports").glob("TEST-*.xml"))
    if not reports:
        problems.append("缺少 Surefire XML")
    counts = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
    discovered = set()
    for report in reports:
        suite = ElementTree.parse(report).getroot()
        for key in counts:
            counts[key] += int(suite.get(key, "0"))
        discovered.update((case.get("classname"), case.get("name"))
                          for case in suite.findall("testcase"))
    if counts["tests"] == 0:
        problems.append("零测试执行")
    if counts["failures"] or counts["errors"]:
        problems.append(f"测试失败或错误：{counts}")
    if strict and counts["skipped"]:
        problems.append(f"跳过 {counts['skipped']} 个用例")
    for source in module["testSources"]:
        if source["classification"] not in ("unit", "mixed"):
            continue
        class_name = source["path"].split("src/test/java/", 1)[-1].removesuffix(".java").replace("/", ".")
        for method in source["methods"]:
            if method["classification"] != "unit":
                continue
            if not any(c == class_name and (n == method["name"] or n.startswith(method["name"] + "("))
                       for c, n in discovered if c and n):
                problems.append(f"用例未发现：{class_name}#{method['name']}")
    if not (output / "jacoco-unit.exec").is_file():
        problems.append("缺少 JaCoCo 执行数据")
    report = output / "jacoco-unit/jacoco.xml"
    coverage = {}
    if not report.is_file():
        problems.append("缺少 JaCoCo XML")
    else:
        root = ElementTree.parse(report).getroot()
        coverage = {node.get("type"): (int(node.get("covered")), int(node.get("missed")))
                    for node in root.findall("counter")}
        classes = {node.get("name"): node for node in root.findall(".//class")}
        for source in module["production"]:
            if source["kind"] in ("interface", "@interface") or source.get("naReason"):
                continue
            class_name = source["path"].split("src/main/java/", 1)[-1].removesuffix(".java")
            if class_name not in classes:
                problems.append(f"生产类缺失：{class_name}")
        if strict:
            for class_name, node in classes.items():
                for counter in node.findall("counter"):
                    if counter.get("type") in ("LINE", "BRANCH", "METHOD") and int(counter.get("missed")):
                        problems.append(f"覆盖率未达标：{class_name} {counter.get('type')}")
    return counts, coverage, problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("baseline", "accept"), required=True)
    parser.add_argument("--scope", default="all")
    parser.add_argument("--evidence", type=Path, help="只检查已有证据，不运行 Maven")
    args = parser.parse_args()
    repos = inventory()
    selected = select(repos, args.scope)
    if not selected:
        raise ValueError("所选范围没有生产源码")
    if args.evidence:
        run_root = args.evidence.resolve()
        run_results = []
    else:
        require_classification(selected)
        if any(repo["repository"] == "metanet4j-component" for repo, _ in selected):
            require_classification([(repo, module) for repo in repos
                                    if repo["repository"] == "metanet4j-component"
                                    for module in repo["modules"] if module["production"]])
        run_root = ROOT / "evidence" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_results = []
        parent_log = run_root / "metanet4j-parent" / "maven.log"
        parent_code, _ = run_maven("metanet4j-parent", ["-N", "install"], parent_log)
        if parent_code:
            raise RuntimeError("父 POM 安装失败")
        chosen_repos = {repo["repository"] for repo, _ in selected}
        for repo_name in REPOSITORIES[1:]:
            if repo_name not in chosen_repos:
                if repo_name in ("metanet4j-base", "metanet4j-sdk") and any(
                        downstream in chosen_repos for downstream in
                        (("metanet4j-sdk", "metanet4j-component") if repo_name == "metanet4j-base"
                         else ("metanet4j-component",))):
                    code, _ = run_maven(repo_name, ["install", "-DskipTests"],
                                        run_root / repo_name / "install.log")
                    if code:
                        raise RuntimeError(f"{repo_name} 上游产物安装失败")
                continue
            chosen_modules = [(repo, module) for repo, module in selected
                              if repo["repository"] == repo_name]
            command_args = ["-Punit-coverage", "clean", "test", "jacoco:report"]
            if args.mode == "accept":
                command_args.append("jacoco:check")
            if repo_name == "metanet4j-component" and args.scope != "all":
                if len(chosen_modules) == 1:
                    command_args[1:1] = ["-pl", chosen_modules[0][1]["path"], "-am"]
            log = run_root / repo_name / "run.log"
            code, command = run_maven(repo_name, command_args, log)
            for repo, module in chosen_modules:
                output = save_artifacts(repo, module, run_root, command, code, log)
                run_results.append((module, output, code))
            if code:
                break
            if repo_name in ("metanet4j-base", "metanet4j-sdk") and any(
                    downstream in chosen_repos for downstream in
                    (("metanet4j-sdk", "metanet4j-component") if repo_name == "metanet4j-base"
                     else ("metanet4j-component",))):
                install_code, _ = run_maven(repo_name, ["install", "-DskipTests"],
                                            run_root / repo_name / "install.log")
                if install_code:
                    raise RuntimeError(f"{repo_name} 验证后产物安装失败")
    failed = False
    if not args.evidence:
        completed = {module["artifactId"] for module, _, _ in run_results}
        for repo, module in selected:
            if module["artifactId"] not in completed:
                run_results.append((module, run_root / repo["repository"] /
                                    module["artifactId"] / "unit", -1))
    for module, output, code in (run_results or [(module, run_root / repo["repository"] /
                                                  module["artifactId"] / "unit", 0)
                                                 for repo, module in selected]):
        counts, coverage, problems = inspect(module, output, args.mode == "accept")
        if code:
            problems.insert(0, f"Maven 退出码 {code}")
        print(f"{module['artifactId']}: tests={counts} coverage={coverage} gaps={len(problems)}")
        for problem in problems:
            print(f"  - {problem}")
        failed |= bool(problems)
    print(f"证据：{run_root}")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, ElementTree.ParseError) as error:
        print(f"验收入口失败：{error}", file=sys.stderr)
        sys.exit(2)
