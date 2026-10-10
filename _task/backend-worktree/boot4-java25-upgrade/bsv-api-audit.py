#!/usr/bin/env python3
"""bsv-api-audit.py — 核对 bsv-replace-api-map.json 与四仓库实际源码。

R0 生成映射，R1—R5 每阶段用它复核「映射是否仍然成立、旧引用是否按映射收口」。
只读：不修改任何仓库。

用法：
  python3 bsv-api-audit.py check          # 核对映射与实际源码（缺项/未收口返回非零）
  python3 bsv-api-audit.py check --json   # 以 JSON 输出结论（供 evidence 记录）

判定口径：
  * 映射覆盖：baseline.json 的 67 个生产旧引用文件与映射条目一一对应；
    逐文件回读 import，任何未被映射认领的旧 import 都算缺项。
  * 目标真实性：replace/adapt/gap 的目标类型与方法必须真实存在于新 SDK 公开面
    （公开方法与 public 字段都接受；新 SDK 大量以字段而非 getter 暴露状态）。
  * 未收口：源码中仍存在旧 import 时报告进度（count > 0 属正常，R5 之后必须为 0）。
  * 清理门禁：--require-clean 时旧 import 必须为 0，否则非零退出（R5/R6 使用）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent
WORK = TASK / "evidence/bsv-replace/r0-api-work"
OLD_PREFIXES = ("io.bitcoinsv", "org.bitcoinj")
IMPORT_RE = re.compile(r"^\s*import\s+(static\s+)?([\w.$]+)\s*;")
FIELD_RE = re.compile(
    r"^\s*public\s+(?:static\s+)?(?:final\s+)?[\w.<>,?\[\] ]+\s+([A-Za-z_$][\w$]*)\s*(?:=|;)")
REPOSITORIES = ("metanet4j-parent", "metanet4j-base", "metanet4j-sdk", "metanet4j-component")


def sdk_surface(sdk_root: Path) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """返回（公开方法名索引，公开字段名索引），键为 FQN。"""
    methods: dict[str, set[str]] = {}
    fields: dict[str, set[str]] = {}
    for path in sdk_root.rglob("*.java"):
        text = path.read_text(errors="replace")
        package = ""
        for line in text.splitlines():
            if line.startswith("package "):
                package = line[len("package "):].strip().rstrip(";")
                break
        fqn = f"{package}.{path.stem}"
        names = {m.group(1) for m in (FIELD_RE.match(l) for l in text.splitlines()) if m}
        if names:
            fields[fqn] = names
    return methods, fields


def scan_old_imports() -> dict:
    """扫描四仓库源码中的旧 import（排除 target/），生产与测试分开统计。"""
    report: dict = {"production": [], "test": [], "byRepository": {}}
    for repo in REPOSITORIES:
        prod, test = [], []
        for path in (TASK / repo).rglob("*.java"):
            if "target" in path.parts:
                continue
            rel = path.relative_to(TASK).as_posix()
            bucket = prod if "/src/main/" in rel else test
            for line_no, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                m = IMPORT_RE.match(line)
                if m and m.group(2).startswith(OLD_PREFIXES):
                    bucket.append(f"{rel}:{line_no} {m.group(2)}")
        report["byRepository"][repo] = {"production": len(prod), "test": len(test)}
        report["production"].extend(prod)
        report["test"].extend(test)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check",))
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    parser.add_argument("--require-clean", action="store_true",
                        help="旧 import 必须为 0（R5/R6 清理门禁）")
    args = parser.parse_args()

    api = json.loads((TASK / "bsv-replace-api-map.json").read_text())
    baseline = json.loads((TASK / "baseline.json").read_text())
    ws_d = json.loads((WORK / "ws-d-new-sdk-index.json").read_text())
    sdk_types = {t["fqn"]: t for t in ws_d["types"]}
    business = set(api["businessNewTypes"])
    _, sdk_fields = sdk_surface(Path(ws_d["sdkRepository"]) / "src/main/java")

    checks: list[dict] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    entries = api["entries"]
    covered = {p for e in entries for p in e["callerFiles"]}
    expected = {p["path"] for p in baseline["oldReferences"]["production"]}
    check("map.coversBaselineFiles", covered == expected,
          f"映射覆盖 {len(covered)}/{len(expected)} 个基线生产文件")

    known = set()
    for e in entries:
        known.add(e["oldSimpleName"])
        known.update(fqn.rsplit(".", 1)[-1] for fqn in e["oldFqns"])
        known.update(fqn.split(".")[-2] + "." + fqn.rsplit(".", 1)[-1]
                     for fqn in e["oldFqns"] if fqn.count(".") >= 2)
    unmapped = []
    for path in sorted(expected):
        for line_no, line in enumerate((TASK / path).read_text(errors="replace").splitlines(), 1):
            m = IMPORT_RE.match(line)
            if m and m.group(2).startswith(OLD_PREFIXES):
                simple = m.group(2).rsplit(".", 1)[-1]
                outer = m.group(2).split(".")[-2]
                if simple not in known and f"{outer}.{simple}" not in known:
                    unmapped.append(f"{path}:{line_no} {m.group(2)}")
    check("map.baselineImportsAllMapped", not unmapped, f"未认领旧 import：{unmapped[:5]}")

    bad_targets = [e["oldSimpleName"] for e in entries
                   if e.get("target") and e["target"]["fqn"] not in sdk_types
                   and e["target"]["fqn"] not in business
                   and e["target"]["source"] != "jdk-or-existing"]
    check("map.targetsExist", not bad_targets, f"目标类型不存在：{bad_targets}")

    sdk_methods = {t["fqn"]: {m["name"] for m in t.get("methods", [])} for t in ws_d["types"]}
    bad_members = []
    for e in entries:
        fqn = (e.get("target") or {}).get("fqn")
        if fqn not in sdk_types:
            continue
        for member in e.get("targetMethods", []):
            if member.get("exists") is True and member["method"] not in sdk_methods[fqn] \
                    and member["method"] not in sdk_fields.get(fqn, set()):
                bad_members.append(f"{e['oldSimpleName']}->{fqn}#{member['method']}")
    check("map.targetMembersExist", not bad_members, f"目标成员未命中：{bad_members}")

    scan = scan_old_imports()
    production, tests = scan["production"], scan["test"]
    check("source.noOldImportsInProduction",
          not production if args.require_clean else True,
          f"生产源码残留旧 import {len(production)} 处"
          + (f"：{production[:3]}" if production else "（已清零）"))
    check("source.noOldImportsInTests",
          not tests if args.require_clean else True,
          f"测试源码残留旧 import {len(tests)} 处"
          + (f"：{tests[:3]}" if tests else "（已清零）"))

    failed = [c for c in checks if not c["ok"]]
    report = {
        "artifact": "bsv-replace-api-map.json",
        "mode": "require-clean" if args.require_clean else "check",
        "checks": checks,
        "oldImportsRemaining": {
            "production": len(scan["production"]), "test": len(scan["test"]),
            "byRepository": scan["byRepository"]},
        "status": "PASS" if not failed else "FAIL",
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for c in checks:
            print(f"  [{'OK' if c['ok'] else 'FAIL'}] {c['check']}：{c['detail']}")
        print(f"  旧 import 残留（生产/测试）：{report['oldImportsRemaining']['production']}"
              f"/{report['oldImportsRemaining']['test']}"
              f"，按仓库 {report['oldImportsRemaining']['byRepository']}")
        print(f"结论：{report['status']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
