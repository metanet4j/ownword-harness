#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
python3 - <<'PYCODE'
from pathlib import Path
import json,subprocess
base=Path.cwd();root=base.parents[2];state=json.loads((base/'feature_list.json').read_text())
assert state['implementationAuthorized']
active=[x['id'] for x in state['features'] if x['status']=='in-progress']
assert active==([state['activeItem']] if state['activeItem'] else [])
for p in state['documents'].values():assert (root/p).is_file(),p
for path in [base/'own-word-web',root/'_task/backend-worktree/ownword-v0.2.0/metanet4j-component']:
 branch=subprocess.check_output(['git','branch','--show-current'],cwd=path,text=True).strip()
 assert branch==state['environment']['branch'],branch
print('任务、文档、授权及前后端分支检查通过；业务验收另行执行。')
PYCODE
