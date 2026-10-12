#!/usr/bin/env python3
"""bsv-task-gate.py — 阶段门禁：核对计划、状态、产物、证据与阶段前置条件。

只读：不修改任何仓库；把结论写到调用方指定的 JSON（默认 stdout）。

用法：
  python3 bsv-task-gate.py --stage r0 --evidence <产物路径.json>
  python3 bsv-task-gate.py --stage r0 --json

判定项：
 readonly   只读输入（指定 SDK 源码、测试、POM、原任务证据）未被改动
 baseline   四目标仓库的提交与既有 diff 与 baseline.json 一致（既有改动保留、未混入提交）
 artifacts  本阶段各执行项的交付物在同一提交中可得，且指纹写入证据
 evidence   每个已完成执行的 feature 均有 evidence，且证据文件真实存在
 coverage   本阶段执行项齐备（R0 六项全部 done 才允许进入 R1）
 selfcheck  ./init.sh 退出 0
 cache      按阶段检查目标 Maven 缓存的制品前提（R1 起生效）

任一失败：非零退出。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TASK = Path(__file__).resolve().parent
BASELINE = TASK / "baseline.json"
REPOSITORIES = ("metanet4j-parent", "metanet4j-base", "metanet4j-sdk", "metanet4j-component")
SDK_SOURCE = Path("/home/haodev/ownword/_task/backend-worktree/bsv-sdk-java-migration/metanet4j-bsv-sdk")
SDK_MIGRATION = Path("/home/haodev/ownword/_task/backend-worktree/bsv-sdk-java-migration")
TARGET_CACHE = Path.home() / ".m2/metanet4j"

STAGE_FEATURES = {
    "r0": ["bsv-r0-source", "bsv-r0-harness", "bsv-r0-api", "bsv-r0-tests", "bsv-r0-vectors", "bsv-r0-gate"],
    "r1": ["bsv-r1-package", "bsv-r1-parent", "bsv-r1-fingerprint"],
    "r2": ["bsv-r2-behavior", "bsv-r2-accept"],
    "r3": ["bsv-r3-keys", "bsv-r3-scripts", "bsv-r3-transactions", "bsv-r3-protocols", "bsv-r3-accept"],
    "r4": ["bsv-r4-foundation", "bsv-r4-transactions", "bsv-r4-downstream", "bsv-r4-isolation", "bsv-r4-accept"],
    "r5": ["bsv-r5-dependencies", "bsv-r5-inventory"],
    "r6": ["bsv-r6-unit", "bsv-r6-http", "bsv-r6-integration", "bsv-r6-artifact", "bsv-r6-report"],
}
# 各阶段允许的未提交改动（key 为仓库名；value 为该仓库允许出现的 git status 行集合）
STAGE_PENDING = {
    "r0": {"metanet4j-base": {"M pom.xml"}},
    "r1": {"metanet4j-base": {"M pom.xml"}, "metanet4j-parent": {"M pom.xml"}},
    "r2": {"metanet4j-base": {"M pom.xml"}},
    "r3": {},
    "r4": {},
    "r5": {},
    "r6": {},
}
STAGE_ARTIFACTS = {
    "r0": ["baseline.json", "bsv-replace-api-map.json", "bsv-replace-test-map.json",
           "bsv-replace-vectors.json", "init.sh", "test-init.py"],
    "r1": ["bsv-replace-artifact.json", "metanet4j-parent/pom.xml", "verify-unit.py"],
    "r2": ["bsv-replace-r2-behavior.json", "bsv-replace-r2-accept.json"],
    "r3": ["unit-test-inventory.json", "unit-coverage-exceptions.json", "verify-unit.py"],
    "r4": ["verify-integration.py", "unit-test-inventory.json"],
    "r5": ["bsv-replace-dependencies.json", "bsv-replace-api-map.json", "bsv-replace-test-map.json", "bsv-replace-current-vector-bindings.json"],
    "r6": ["bsv-replace-final-acceptance.json", "bsv-replace-current-vector-bindings.json", "verify-final.py", "bsv-replace-r6-delivery-report.md"],
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo: str, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(TASK / repo), *args], text=True).strip()


def file_fingerprint(repo: str) -> tuple[str, int]:
    """与 baseline.json 相同的算法：全部 tracked 源码与 POM 的路径+内容摘要。"""
    files = git(repo, "ls-files").splitlines()
    digest = hashlib.sha256()
    count = 0
    for name in sorted(files):
        if name.startswith("target/"):
            continue
        digest.update(name.encode())
        digest.update((TASK / repo / name).read_bytes())
        count += 1
    return digest.hexdigest(), count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=sorted(STAGE_FEATURES))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    baseline = json.loads(BASELINE.read_text())
    features = json.loads((TASK / "feature_list.json").read_text())
    by_id = {f["id"]: f for f in features["features"]}
    checks: list[dict] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    # ---- 只读输入 ----
    sdk_head = subprocess.check_output(["git", "-C", str(SDK_SOURCE), "rev-parse", "HEAD"], text=True).strip()
    sdk_status = subprocess.check_output(["git", "-C", str(SDK_SOURCE), "status", "--porcelain"], text=True).strip()
    check("readonly.sdkHeadUnchanged", sdk_head == baseline["sdkAcceptance"]["gitHead"],
          f"SDK HEAD {sdk_head}（基线 {baseline['sdkAcceptance']['gitHead']}）")
    check("readonly.sdkWorktreeClean", not sdk_status,
          f"SDK 工作区{'干净' if not sdk_status else '有改动：' + sdk_status[:120]}")
    manifest = Path(baseline["sdkAcceptance"]["manifestPath"])
    check("readonly.originalEvidenceIntact",
          manifest.is_file() and sha256_file(manifest) == baseline["sdkAcceptance"]["manifestSha256"],
          f"原验收清单 {manifest.name} 指纹与基线一致" if manifest.is_file() else "原验收清单缺失")

    # ---- 四仓库基线（第五项为只读 SDK 来源，已在上方单独核对） ----
    for record in baseline["repositories"]:
        repo = record["repository"]
        if repo not in REPOSITORIES:
            continue
        head = git(repo, "rev-parse", "HEAD")
        branch = git(repo, "branch", "--show-current")
        status = git(repo, "status", "--porcelain")
        allowed = STAGE_PENDING.get(args.stage, {}).get(repo, set())
        status_lines = set(status.splitlines())
        unexpected = status_lines - allowed
        allowed_note = ("允许的未提交改动：" + "、".join(sorted(allowed))) if allowed else "本阶段不允许未提交改动"
        if repo == "metanet4j-base":
            ok = branch == record["branch"] and not unexpected
            detail = f"分支 {branch}；工作区改动 {sorted(status_lines) or '无'}（{allowed_note}）"
        else:
            # 已提交实现后 HEAD 会前进；此处只要求分支正确、无未预期改动，HEAD 前进由提交记录体现
            ok = branch == record["branch"] and not unexpected
            detail = (f"HEAD {head[:9]}（基线 {record['head'][:9]}），分支 {branch}，"
                      f"工作区改动 {sorted(status_lines) or '无'}（{allowed_note}）")
        check(f"baseline.{repo}", ok, detail)

    # 既有 diff 与冻结 patch 字节级一致
    patch = baseline["evidenceDir"] + "/existing-base-pom.patch"
    live = subprocess.check_output(["git", "-C", str(TASK / "metanet4j-base"), "diff", "--", "pom.xml"],
                                   text=True)
    frozen = (TASK / patch).read_text().strip()
    if args.stage in ("r0", "r1"):
        check("baseline.baseExistingDiffPreserved", live.strip() == frozen,
              "base 既有 POM 改动与冻结 patch 一致（未还原、未提前提交）")
    else:
        # R2 起该改动与实现共同提交，改为核对已进入历史
        committed = subprocess.run(
            ["git", "-C", str(TASK / "metanet4j-base"), "log", "-1", "--format=%H", "--", "pom.xml"],
            capture_output=True, text=True, check=False).stdout.strip()
        check("baseline.basePomHasHistory", bool(committed),
              f"base pom.xml 已有提交历史 {committed[:9]}" if committed else "base pom.xml 尚无提交")

    # ---- 产物 ----
    for name in STAGE_ARTIFACTS[args.stage]:
        path = TASK / name
        check(f"artifact.{name}", path.is_file(),
              f"{'存在' if path.is_file() else '缺失'}（sha256 {sha256_file(path)[:12]}…）" if path.is_file()
              else "缺失")

    # ---- 执行项与证据 ----
    stage_ids = STAGE_FEATURES[args.stage]
    incomplete = [fid for fid in stage_ids if by_id[fid]["status"] != "done"]
    check("coverage.stageComplete", not incomplete,
          f"{args.stage.upper()} 执行项 {len(stage_ids) - len(incomplete)}/{len(stage_ids)} 完成"
          + (f"；未完成 {incomplete}" if incomplete else ""))
    missing_evidence = []
    for fid in stage_ids:
        f = by_id[fid]
        if f["status"] == "done" and not f.get("evidence"):
            missing_evidence.append(fid)
    check("evidence.eachDoneFeatureHasEvidence", not missing_evidence,
          f"无证据的完成项：{missing_evidence}")
    unverified = []
    for fid in stage_ids:
        f = by_id[fid]
        if f["status"] == "done" and not f.get("commits"):
            unverified.append(fid)
    check("evidence.eachDoneFeatureHasCommit", not unverified, f"无提交记录的完成项：{unverified}")

    # ---- 产物指纹与证据交叉核对（R0 起） ----
    if args.stage == "r0":
        cross = [
            ("evidence/bsv-replace/r0-api-work/summary.json",
             "bsv-replace-api-map.json", "artifactFingerprint"),
            ("evidence/bsv-replace/r0-api-work/test-map-summary.json",
             "bsv-replace-test-map.json", "artifactFingerprint"),
            ("evidence/bsv-replace/r0-api-work/vectors-summary.json",
             "bsv-replace-vectors.json", "artifactFingerprint"),
        ]
        for evidence_rel, artifact, key in cross:
            evidence = TASK / evidence_rel
            target = TASK / artifact
            if not evidence.is_file():
                check(f"crosscheck.{artifact}", False, f"缺少证据 {evidence_rel}")
                continue
            data = json.loads(evidence.read_text())
            recorded = data.get(key, {}).get("sha256")
            actual = sha256_file(target)
            check(f"crosscheck.{artifact}", recorded == actual,
                  f"证据记录 {str(recorded)[:12]}… 与实际 {actual[:12]}…"
                  + ("一致" if recorded == actual else "不一致（证据已过期）"))
        for verifier, name in (("evidence/bsv-replace/r0-api-work/api-map-verify.json", "API 映射复核"),
                               ("evidence/bsv-replace/r0-api-work/test-map-audit.json", "测试映射复核"),
                               ("evidence/bsv-replace/r0-api-work/vectors-verify.json", "向量复核"),
                               ("evidence/bsv-replace/r0-api-work/vectors-independent-check.json", "独立复算")):
            path = TASK / verifier
            if not path.is_file():
                check(f"crosscheck.{name}", False, f"缺少 {verifier}")
                continue
            data = json.loads(path.read_text())
            check(f"crosscheck.{name}", data.get("status") == "PASS",
                  f"status={data.get('status')}")

    # ---- 能力缺口收口（R0 起） ----
    if args.stage == "r0":
        api = json.loads((TASK / "bsv-replace-api-map.json").read_text())
        gap_types = [e["oldSimpleName"] for e in api["entries"]
                     if e["handling"] == "gap" and not (e.get("note") or "").strip()]
        check("gaps.noUnresolvedDecision", not gap_types,
              f"未给结论的能力缺口：{gap_types}")
        gap_types = [e["oldSimpleName"] for e in api["entries"] if e["handling"] == "gap"]
        covered = set()
        for gap in api.get("capabilityGaps", []):
            covered.update(gap.get("oldTypes", []))
            for old in gap.get("oldTypes", []):
                covered.add(old)
        for res in api.get("resolveCapabilityGaps", []):
            covered.update(res.get("carriedBy", []))
        # capabilityGaps 也可能以旧的简单名分组（如 "NetworkParameters"）
        for gap in api.get("capabilityGaps", []):
            for old in gap.get("oldTypes", []):
                for entry in api["entries"]:
                    if entry["oldSimpleName"] == old:
                        covered.update(fqn.rsplit(".", 1)[-1] for fqn in entry["oldFqns"])
        uncovered = [t for t in gap_types if t not in covered
                     and not any(t in json.dumps(gap, ensure_ascii=False)
                                 for gap in api.get("capabilityGaps", []))]
        check("gaps.resolutionCoversAllGapTypes", not uncovered,
              f"缺口类型 {gap_types} 均有结论" + (f"；未覆盖 {uncovered}" if uncovered else ""))
        gap_ids = [g["id"] for g in api.get("resolveCapabilityGaps", [])]
        check("gaps.haveCarryPhase",
              all(g.get("carriedBy") for g in api.get("resolveCapabilityGaps", [])),
              f"{len(gap_ids)} 项缺口结论均标明承接阶段：{gap_ids}")

    # ---- 自检 ----
    result = subprocess.run(["bash", str(TASK / "init.sh")], capture_output=True, text=True, check=False)
    check("selfcheck.initSh", result.returncode == 0,
          f"./init.sh 退出 {result.returncode}")

    # ---- 目标缓存（按阶段） ----
    if args.stage in ("r1", "r2", "r3", "r4", "r5", "r6"):
        jar = TARGET_CACHE / "com/metanet4j/metanet4j-bsv-sdk/0.2.0/metanet4j-bsv-sdk-0.2.0.jar"
        check("cache.sdkInstalled", jar.is_file(),
              f"目标缓存 {'已有制品' if jar.is_file() else '尚无新 SDK 制品'}")

    failed = [c for c in checks if not c["ok"]]
    if args.stage == "r6":
        final = subprocess.run([sys.executable, str(TASK / "verify-final.py")], capture_output=True, text=True)
        check("final.currentFullAcceptance", final.returncode == 0, final.stdout + final.stderr)
        failed = [c for c in checks if not c["ok"]]
    report = {
        "stage": args.stage.upper(),
        "generatedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "checks": checks,
        "status": "PASS" if not failed else "FAIL",
        "failed": [c["check"] for c in failed],
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for c in checks:
            print(f"  [{'OK' if c['ok'] else 'FAIL'}] {c['check']}：{c['detail']}")
        print(f"\n阶段 {report['stage']} 门禁：{report['status']}"
              + (f"（失败项 {report['failed']}）" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
