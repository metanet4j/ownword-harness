#!/usr/bin/env python3
"""按模块运行单元测试并核对 Surefire 与 JaCoCo 证据。"""

import argparse
import hashlib
import json
import os
import re
import shlex
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
# BSV 能力层制品：运行元数据保存其指纹，严格验收时与固定清单及已安装制品比对。
# 同坐标制品被覆盖后，旧证据必须失效而不是静默沿用。
SDK_COORDINATE = ("com.metanet4j", "metanet4j-bsv-sdk", "0.2.0")
SDK_MANIFEST = ROOT / "bsv-replace-artifact.json"
SDK_CACHE = Path.home() / ".m2/metanet4j"


def declared_tests(source):
    """清点 Java 中真实声明的 Jupiter 测试方法，不把夹具方法当成测试。"""
    source = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
    pattern = (r"(?m)^\s*@(?:Test|ParameterizedTest|RepeatedTest|TestFactory|TestTemplate)\b"
               r"(?:\([^)]*\))?\s*(?:@\w+(?:\([^)]*\))?\s*)*"
               r"(?:(?:public|protected|private|static|final)\s+)*[\w<>\[\],.?]+\s+(\w+)\s*\(")
    return set(re.findall(pattern, source))


def sdk_artifact() -> dict:
    """返回已安装 SDK 制品的坐标、路径与 SHA-256；缺失时 hashes 为 None。"""
    group, artifact, version = SDK_COORDINATE
    base = SDK_CACHE / group.replace(".", "/") / artifact / version
    jar, pom = base / f"{artifact}-{version}.jar", base / f"{artifact}-{version}.pom"
    result = {"coordinate": ":".join(SDK_COORDINATE), "jarPath": str(jar), "pomPath": str(pom),
              "jarSha256": None, "pomSha256": None, "installed": jar.is_file() and pom.is_file()}
    for key, path in (("jarSha256", jar), ("pomSha256", pom)):
        if path.is_file():
            result[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def sdk_manifest() -> dict:
    """读取 R1 绑定的固定制品清单；缺失时返回空。"""
    if not SDK_MANIFEST.is_file():
        return {}
    data = json.loads(SDK_MANIFEST.read_text())
    artifact = data.get("artifact", {})
    cache = data.get("installedToTargetCache", {})
    return {"coordinate": ":".join(SDK_COORDINATE),
            "jarSha256": (artifact.get("sourceJar") or {}).get("sha256"),
            "pomSha256": (artifact.get("sourcePom") or {}).get("sha256"),
            "installedJarSha256": (cache.get("jar") or {}).get("sha256"),
            "installedPomSha256": (cache.get("pom") or {}).get("sha256"),
            "sourceFingerprint": (data.get("source") or {}).get("srcMainAndPomSha256"),
            "gitHead": (data.get("source") or {}).get("gitHead")}


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
            for entry in module["testSources"]:
                source = (ROOT / repo["repository"] / entry["path"]).read_text()
                actual_methods = declared_tests(source)
                listed_methods = {method["name"] for method in entry["methods"]}
                if actual_methods != listed_methods:
                    raise ValueError(f"{entry['path']} 测试方法清单不一致："
                                     f"缺少 {sorted(actual_methods - listed_methods)}；"
                                     f"多列 {sorted(listed_methods - actual_methods)}")
            if module.get("noExecutableReason") and (module["testSources"] or any(
                    item["kind"] not in ("interface", "@interface") for item in module["production"])):
                raise ValueError(f"{module['artifactId']} 无可执行代码标记与源码清单冲突")
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
    invocation = {"command": command, "javaHome": str(JDK),
                  "startedAt": datetime.now(timezone.utc).timestamp()}
    if "clean" in args and "test" in args:
        modules = [module for repo in inventory() if repo["repository"] == repo_name
                   for module in repo["modules"]]
        invocation["startFingerprints"] = {
            module["artifactId"]: fingerprint(repo_name, module) for module in modules}
        invocation["startHead"] = subprocess.check_output(
            ["git", "-C", str(ROOT / repo_name), "rev-parse", "HEAD"], text=True).strip()
    invocation_path = log_path.with_suffix(".command.json")
    invocation_path.write_text(json.dumps(invocation, ensure_ascii=False, indent=2) + "\n")
    with log_path.open("w") as log:
        result = subprocess.run(command, cwd=ROOT / repo_name, env=environment,
                                stdout=log, stderr=subprocess.STDOUT, check=False)
    invocation.update(exitCode=result.returncode, finishedAt=datetime.now(timezone.utc).timestamp())
    invocation_path.write_text(json.dumps(invocation, ensure_ascii=False, indent=2) + "\n")
    print(f"{repo_name}: exit={result.returncode}，日志 {log_path}", flush=True)
    return result.returncode, command


def fingerprint(repo_name, module):
    digest = hashlib.sha256()
    directory = ROOT / repo_name / module["path"]
    sources = [path for kind in ("main", "test")
               for path in (directory / "src" / kind).rglob("*") if path.is_file()]
    for path in sorted(sources):
        digest.update(path.relative_to(ROOT / repo_name).as_posix().encode())
        digest.update(path.read_bytes())
    poms = {ROOT / repo_name / module["path"] / "pom.xml", ROOT / "metanet4j-parent/pom.xml"}
    if repo_name == "metanet4j-component":
        poms.add(ROOT / repo_name / "pom.xml")
    for pom in sorted(poms):
        digest.update(pom.relative_to(ROOT).as_posix().encode())
        digest.update(pom.read_bytes())
    return digest.hexdigest()


def save_artifacts(repo, module, run_root, command, exit_code, log_path):
    target = ROOT / repo["repository"] / module["path"] / "target"
    output = run_root / repo["repository"] / module["artifactId"] / "unit"
    output.mkdir(parents=True, exist_ok=True)
    invocation = json.loads(log_path.with_suffix(".command.json").read_text())
    started = invocation["startedAt"]
    reports = target / "surefire-reports"
    if reports.exists():
        for report in reports.iterdir():
            if report.is_file() and report.stat().st_mtime >= started:
                (output / "surefire-reports").mkdir(exist_ok=True)
                shutil.copy2(report, output / "surefire-reports" / report.name)
    coverage = target / "site/jacoco-unit"
    if (coverage / "jacoco.xml").is_file() and (coverage / "jacoco.xml").stat().st_mtime >= started:
        shutil.copytree(coverage, output / "jacoco-unit", dirs_exist_ok=True)
    if (target / "jacoco-unit.exec").is_file() and (target / "jacoco-unit.exec").stat().st_mtime >= started:
        shutil.copy2(target / "jacoco-unit.exec", output / "jacoco-unit.exec")
    if log_path.exists():
        shutil.copy2(log_path, output / "maven.log")
    head = subprocess.check_output(["git", "-C", str(ROOT / repo["repository"]),
                                    "rev-parse", "HEAD"], text=True).strip()
    metadata = {"head": head, "command": command, "exitCode": exit_code, "invocation": invocation,
                "artifactId": module["artifactId"], "repository": repo["repository"],
                "sourceFingerprint": fingerprint(repo["repository"], module),
                "sdkArtifact": sdk_artifact()}
    (output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    return output


def coverage_exceptions():
    path = ROOT / "unit-coverage-exceptions.json"
    if not path.is_file():
        raise ValueError("缺少覆盖率例外清单 unit-coverage-exceptions.json")
    data = json.loads(path.read_text())
    return {artifact: {entry["class"]: entry for entry in module["entries"]}
            for artifact, module in data.get("modules", {}).items()}


def method_misses(node):
    missed = {}
    for method in node.findall("method"):
        line_missed = method_missed = branch_missed = 0
        for counter in method.findall("counter"):
            if counter.get("type") == "LINE":
                line_missed = int(counter.get("missed"))
            elif counter.get("type") == "METHOD":
                method_missed = int(counter.get("missed"))
            elif counter.get("type") == "BRANCH":
                branch_missed = int(counter.get("missed"))
        if line_missed or method_missed or branch_missed:
            # 键含行号：同名重载方法（如 createTempFile 的三个重载）必须逐项区分，否则后者会覆盖前者
            missed[f"{method.get('name')}:{method.get('line')}"] = {
                "method": method.get("name"), "line": int(method.get("line")),
                "lineMissed": line_missed, "methodMissed": method_missed,
                "branchMissed": branch_missed}
    return missed


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
        command = shlex.split(command) if isinstance(command, str) else command
        command_text = " ".join(command)
        if "clean" not in command or "test" not in command:
            problems.append("命令未包含 clean test")
        if "-DskipTests" in command_text or "maven.test.skip" in command_text \
                or "maven.test.failure.ignore=true" in command_text:
            problems.append("命令跳过测试")
        if strict:
            if "-Punit-coverage" not in command or "jacoco:check" not in command:
                problems.append("命令未启用严格覆盖率检查")
            if "-DexcludedGroups=integration,external" not in command:
                problems.append("命令未明确单元测试分层")
            artifact = sdk_artifact()
            expected = sdk_manifest()
            if not expected:
                problems.append("缺少固定 SDK 制品清单")
            if not artifact["installed"]:
                problems.append("目标缓存缺少 SDK 制品：" + artifact["coordinate"])
            elif expected:
                if artifact["jarSha256"] != expected.get("installedJarSha256") \
                        or artifact["pomSha256"] != expected.get("installedPomSha256"):
                    problems.append(
                        "SDK 制品指纹与 R1 绑定不一致（同坐标制品可能已被覆盖）："
                        f"实测 jar={str(artifact['jarSha256'])[:12]}… pom={str(artifact['pomSha256'])[:12]}…；"
                        f"绑定 jar={str(expected.get('installedJarSha256'))[:12]}… "
                        f"pom={str(expected.get('installedPomSha256'))[:12]}…")
            recorded = (metadata.get("sdkArtifact") or {}).get("jarSha256")
            if recorded != artifact["jarSha256"]:
                problems.append("证据记录的 SDK 制品指纹与当前已安装制品不一致")
            if (metadata.get("sdkArtifact") or {}).get("pomSha256") != artifact["pomSha256"]:
                problems.append("证据记录的 SDK POM 指纹与当前已安装制品不一致")
            repo_name = metadata.get("repository", "")
            invocation = metadata.get("invocation", {})
            if invocation.get("startFingerprints", {}).get(module["artifactId"]) != metadata.get("sourceFingerprint"):
                problems.append("执行前后源码或测试资源发生变化，证据失效")
            if invocation.get("startHead") != metadata.get("head"):
                problems.append("执行前后提交发生变化，证据失效")
            if repo_name not in REPOSITORIES or metadata.get("sourceFingerprint") != fingerprint(repo_name, module):
                problems.append("证据与当前源码不一致")
            elif metadata.get("head") != subprocess.check_output(
                    ["git", "-C", str(ROOT / repo_name), "rev-parse", "HEAD"], text=True).strip():
                problems.append("证据与当前提交不一致")
    if module.get("noExecutableReason"):
        return {key: 0 for key in ("tests", "failures", "errors", "skipped")}, {}, problems
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
        class_name = source["path"].split("src/test/java/", 1)[-1].removesuffix(".java").replace("/", ".")
        if strict and source["classification"] == "invalid-test-signature":
            problems.append(f"测试签名无效：{class_name}")
        if strict and source["classification"] == "disabled":
            problems.append(f"测试被禁用：{class_name}")
        for method in source["methods"]:
            found = any(c == class_name and (n == method["name"] or n.startswith(method["name"] + "("))
                        for c, n in discovered if c and n)
            if method["classification"] == "unit" and not found:
                problems.append(f"用例未发现：{class_name}#{method['name']}")
            if method["classification"] in ("integration", "external", "disabled") and found:
                problems.append(f"非单元用例混入：{class_name}#{method['name']}")
            if strict and method["classification"] == "external" and not (
                    method.get("replacementTests") or method.get("manualReason")):
                problems.append(f"外部用例未映射去向：{class_name}#{method['name']}")
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
            exceptions = coverage_exceptions().get(module["artifactId"], {})
            for class_name, node in classes.items():
                counters = {counter.get("type"): int(counter.get("missed"))
                            for counter in node.findall("counter")}
                missed_methods = method_misses(node)
                expected = exceptions.get(class_name)
                if expected is None:
                    for counter_type in ("LINE", "BRANCH", "METHOD"):
                        if counters.get(counter_type):
                            problems.append(f"覆盖率未达标：{class_name} {counter_type}")
                    continue
                recorded = {f"{item['method']}:{item['line']}": {
                    "method": item["method"], "line": item["line"], "lineMissed": item["lineMissed"],
                    "methodMissed": item["methodMissed"],
                    "branchMissed": item.get("branchMissed", 0)}
                    for item in expected["missed"]}
                if counters.get("BRANCH", 0) != sum(item.get("branchMissed", 0) for item in expected["missed"]):
                    problems.append(f"覆盖率例外分支计数不符：{class_name}")
                if missed_methods != recorded:
                    problems.append(f"覆盖率例外清单不符：{class_name} 实测 {missed_methods or '无'}，"
                                    f"记录 {recorded}")
                elif counters.get("LINE") != sum(item["lineMissed"] for item in recorded.values()) \
                        or counters.get("METHOD") != sum(item["methodMissed"] for item in recorded.values()):
                    # JaCoCo 的类级 LINE 计数不会重复计入 lambda 体内的行，而逐方法之和会，
                    # 因此只有当类级计数大于逐方法和（存在重叠）且不大于含外层方法的累计时才视为口径差异；
                    # 小于逐方法和说明登记值被改小，仍要报错。
                    recorded_line = sum(item["lineMissed"] for item in recorded.values())
                    class_line = counters.get("LINE", 0)
                    overlapping = any("lambda$" in item["method"] for item in recorded.values())
                    if not (overlapping and recorded_line > class_line):
                        problems.append(f"覆盖率例外类级计数不符：{class_name}")
            for class_name in exceptions:
                if class_name not in classes:
                    problems.append(f"覆盖率例外清单未命中实测数据：{class_name}")
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
            command_args = ["-Punit-coverage", "clean", "test", "jacoco:report",
                            "-DexcludedGroups=integration,external"]
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
