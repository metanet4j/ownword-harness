#!/usr/bin/env bash
set -euo pipefail
task_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
workspace_root=$(cd -- "$task_root/../../.." && pwd)
export JAVA_HOME=/home/haodev/.sdkman/candidates/java/25.0.4.1-tem
"$JAVA_HOME/bin/java" -version
node --version
python3 - "$workspace_root" "$task_root" <<'CHECK'
import json, pathlib, subprocess, sys
root, task = map(pathlib.Path, sys.argv[1:])
source = next(x for x in json.loads((root/'reference/sources.lock.json').read_text())['sources'] if x['path']=='reference/js-junglebus')
repo = root/source['path']
def git(*args): return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
assert git('rev-parse','HEAD') == source['commit'], '原始源码版本不匹配'
assert not git('status','--porcelain'), '原始源码有改动'
features = json.loads((task/'feature_list.json').read_text())['features']
assert sum(x['status']=='in-progress' for x in features) <= 1, '存在多个进行中事项'
java_repo = task/'metanet4j-junglebus'
if (java_repo/'.git').exists():
    branch=subprocess.check_output(['git','-C',str(java_repo),'branch','--show-current'],text=True).strip()
    assert branch=='feature/java25', f'Java 工程分支不匹配：{branch}'
print('环境、固定上游和任务状态检查通过。')
CHECK
