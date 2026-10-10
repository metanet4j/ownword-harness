#!/usr/bin/env python3
"""在临时任务副本核对自检的通过、拒绝与失败退出，不修改仓库状态。"""
import copy
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    source = json.loads((ROOT / "feature_list.json").read_text())
    checked = 0
    with tempfile.TemporaryDirectory(prefix="bsv-init-check-") as temp:
        parent = Path(temp)
        task = parent / "task"
        task.mkdir()
        shutil.copy2(ROOT / "init.sh", task / "init.sh")
        for name in ("AGENTS.md", "mvn-command.md"):
            (parent / name).symlink_to(ROOT.parent / name)
        for name in ("AGENTS.md", "progress.md", "session-handoff.md"):
            (task / name).symlink_to(ROOT / name)
        for repo in ("parent", "base", "sdk", "component"):
            name = f"metanet4j-{repo}"
            (task / name).symlink_to(ROOT / name, target_is_directory=True)
        (task / "doc").symlink_to(ROOT / "doc", target_is_directory=True)

        def check(name, mutate=None, text=None, args=(), exit_code=1, expected=""):
            nonlocal checked
            data = copy.deepcopy(source)
            if mutate:
                mutate(data)
            (task / "feature_list.json").write_text(
                text if text is not None else json.dumps(data, ensure_ascii=False)
            )
            result = subprocess.run(
                ["bash", str(task / "init.sh"), *args],
                text=True, capture_output=True, timeout=30,
            )
            output = result.stdout + result.stderr
            assert result.returncode == exit_code, (name, result.returncode, output)
            assert expected in output, (name, output)
            checked += 1
            print(f"PASS {name}: exit={result.returncode}")

        check("valid-state", exit_code=0, expected="feature 状态、依赖、完成证据及阶段门禁一致")
        check("reject-full", args=("--full",), exit_code=2, expected="仅自检")
        check("invalid-json", text="{", expected="执行状态异常")
        check("missing-plan", lambda d: d.update(planDoc="missing.md"), expected="planDoc 未指定有效文件")
        check("duplicate-id", lambda d: d["features"].append(d["features"][0]), expected="feature ID 重复")
        check("cycle", lambda d: d["features"][0].update(dependencies=[d["features"][0]["id"]]), expected="依赖有环")
        check("unknown-dependency", lambda d: d["features"][0].update(dependencies=["missing"]), expected="依赖 feature 不存在")
        check("wrong-active", lambda d: d.update(activeItem="missing"), expected="activeItem 与唯一执行项不符")
        check("missing-evidence", lambda d: d["features"][0].update(evidence=[]), expected="完成但无证据")
        check("premature-stage", lambda d: d["stages"][0].update(status="done"), expected="阶段状态不符")
        check("unknown-next", lambda d: d.update(nextItem="missing"), expected="nextItem 不存在")
        check("stage-count", lambda d: d["stages"][0].update(progress={"total":6,"done":6}), expected="阶段计数不符")
    print(f"{checked} checks passed；仅自检门禁验证，未构建或执行业务测试。")


if __name__ == "__main__":
    main()
