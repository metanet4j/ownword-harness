"""核对任务登记和实际版本 worktree，不启动服务或修改仓库。"""
import json
import subprocess
import sys
from pathlib import Path

task = Path(__file__).resolve().parent
workspace = task.parents[2]
state = json.loads((task / "feature_list.json").read_text())
active = [f for f in state["features"] if f["status"] == "in-progress"]
assert len(active) <= 1, "同时存在多个进行中事项"
assert state["activeItem"] == (active[0]["id"] if active else None)
ids = {f["id"] for f in state["features"]}
assert len(ids) == len(state["features"])
for f in state["features"]:
    assert f["status"] in state["allowedStatuses"]
    assert set(f["dependencies"]) <= ids
    assert f["doneCriteria"]
for path in state["documents"].values():
    assert (workspace / path).is_file(), path
assert len(state["acceptance"]) == 10
if "--plan" not in sys.argv:
    frontend = task / state["environment"]["frontendWorktree"]
    actual = subprocess.check_output(
        ["git", "-C", str(frontend), "branch", "--show-current"], text=True
    ).strip()
    assert actual == state["environment"]["frontendBranch"], actual
    assert (frontend / ".git").is_file(), "前端必须是独立 worktree"
    backend = workspace / state["environment"]["backendTask"]
    assert (backend / "environment.json").is_file(), "缺少后端环境登记"
    env = json.loads((backend / "environment.json").read_text())
    for r in env["repositories"]:
        p = backend / r["name"]
        actual = subprocess.check_output(
            ["git", "-C", str(p), "branch", "--show-current"], text=True
        ).strip()
        assert actual == state["environment"]["backendBranch"], actual
        subprocess.check_call(["git", "-C", str(p), "merge-base", "--is-ancestor", r["baseline"], "HEAD"])
print("任务、文档及所选环境检查通过；不表示业务实现或集成验收通过。")
