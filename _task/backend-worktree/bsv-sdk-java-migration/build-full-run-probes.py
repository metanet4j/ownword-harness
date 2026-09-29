#!/usr/bin/env python3
"""扫描局部登记与适配器，生成全量运行的探针分派表 full-run-probes.json。

用法：
    python3 build-full-run-probes.py [--output full-run-probes.json] [--quiet]

只读 full-evidence-locals.json（共享 flock 读取，避免与并行登记读到写坏一半）与各采集驱动源码，
不改任何既有登记、探针与适配器。

每个原文件条目形如：

    {"probe": "capture-signature-inputs.cjs", "env": "MIGRATION_SIGNATURE_TS_OBSERVATIONS",
     "probes": [{"local": "signature", "probe": "...", "env": "...", "mode": "raw",
                 "raw": "signature.calls.raw.jsonl",
                 "outputs": {"MIGRATION_..._TS_OBSERVATIONS": "signature.calls.raw.jsonl"},
                 "corpus": {"MIGRATION_..._RANDOM": "/abs/path/random.json"},
                 "values": {"MIGRATION_BN_VARIANT": "arithmetic"}}]}

探针三类：
    direct    探针直接把本轮最终行写进 EVIDENCE_INPUTS_PATH；
    raw       探针把原始轨迹写进 MIGRATION_*_OBSERVATIONS／_TS_INPUTS／_FRAMES 等环境变量，
              采集后由 emit 段（取自驱动源码里的 prepare-*-inputs.py emit-ts 调用）转换；
    external  raw 之外还要冻结语料（corpus）或固定取值（values，例如 MIGRATION_BN_VARIANT）。

探针来源优先级：*-locals.py 登记表 → 与局部同名的 capture-<局部>.cjs → 登记里的 capture 适配器
→ 按原文件匹配的采集驱动（含 *-local-gate.py）→ 驱动里的 PROBE 常量。
无法唯一确定的条目写进 pending／unresolved 并打印，不瞎猜。
"""
import argparse
import ast
import fcntl
import importlib.util
import json
import re
from pathlib import Path

TASK = Path(__file__).resolve().parent
CONFIG = TASK / 'full-evidence-locals.json'
LOCK = TASK / '.cache/locals.lock'
CATALOG = TASK / 'module-tests.json'

# 全量运行自身会提供的环境变量，采集驱动不负责赋值。
GLOBAL_ENVS = {
    'MIGRATION_PARITY_TS_OBSERVATIONS', 'MIGRATION_NETWORK_LOG', 'MIGRATION_PARITY_JAVA_OUTPUT',
    'EVIDENCE_RUN_ID', 'EVIDENCE_SIDE', 'EVIDENCE_INPUTS_PATH', 'EVIDENCE_ASSERTIONS_PATH',
    'EVIDENCE_INPUT_PLAN', 'MIGRATION_FULL_RUN_DIR', 'MIGRATION_FULL_PROBES',
    'MIGRATION_FULL_EMIT_DIR', 'MIGRATION_FULL_RAW_SUFFIX',
}
GLOBAL_SETUP = ('ts-offline-guard.cjs', 'capture-parity.cjs')


def read_locked(path):
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK, 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        try:
            return json.loads(Path(path).read_text())
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def load_locals_modules():
    """读取 *-locals.py 登记表；标准局部优先于驱动源码推断。"""
    entries, modules = {}, []
    for path in sorted(TASK.glob('*-locals.py')):
        spec = importlib.util.spec_from_file_location('locals_' + path.stem.replace('-', '_'), path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            continue
        table = getattr(module, 'LOCALS', None)
        if not isinstance(table, dict):
            continue
        modules.append(path.name)
        for name, entry in table.items():
            if isinstance(entry, dict) and 'file' in entry and 'probe' in entry:
                entries[name] = dict(entry, module=path.name)
    return entries, modules


def assigned_vars(tree):
    table = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            table.setdefault(node.targets[0].id, node.value)
    return table


def variant_tables(tree):
    tables = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Dict):
            continue
        rows = {}
        for key, value in zip(node.value.keys, node.value.values):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                continue
            if isinstance(value, ast.Tuple):
                parts = [part.value for part in value.elts
                         if isinstance(part, ast.Constant) and isinstance(part.value, str)]
                if parts:
                    rows[key.value] = parts
        if rows:
            tables.append(rows)
    return tables


def pick_variant(tables, local_file):
    """按原文件定位变体行：返回 (变体名, 前缀/分组)。"""
    for table in tables:
        for key, parts in table.items():
            if any(part == local_file or local_file.endswith('/' + part) for part in parts):
                prefix = next((part for part in parts if re.fullmatch(r'[a-z][a-z0-9\-]*', part)), None)
                return key, prefix
    return None, None


def probe_envs(path):
    text = Path(path).read_text(errors='replace')
    return set(re.findall(r'process\.env\.([A-Z0-9_]+)', text)) \
        | set(re.findall(r'process\.env\[[\'"]([A-Z0-9_]+)[\'"]\]', text))


def probe_direct(path):
    """探针是否自己把最终行写进 EVIDENCE_INPUTS_PATH。"""
    text = Path(path).read_text(errors='replace')
    if not re.search(r'process\.env(?:\.|\[[\'"])EVIDENCE_INPUTS_PATH', text):
        return False
    return bool(re.search(r'(appendFileSync|writeFileSync|createWriteStream|writeFile|openSync)'
                          r'\s*\(\s*[A-Za-z_$][\w$]*', text))


class Resolver:
    """把驱动里的路径表达式解析成 runDir 输出、冻结语料、固定取值，或明确的解析失败。"""

    def __init__(self, path, local_file, plan_dir, replay):
        self.path = path
        self.text = path.read_text(errors='replace')
        self.tree = ast.parse(self.text)
        self.vars = assigned_vars(self.tree)
        self.variant, self.prefix = pick_variant(variant_tables(self.tree), local_file)
        self.local_file = local_file
        self.plan_dir = Path(plan_dir)
        self.replay = Path(replay).resolve() if replay else None
        self.dynamic_keys = {}

    def source(self, node):
        return ast.get_source_segment(self.text, node) or ''

    def existing(self, name):
        for base in (TASK, self.plan_dir):
            candidate = base / name
            if candidate.is_file():
                return candidate
        return None

    def eval(self, node, depth=0):  # noqa: C901 - 受限表达式的显式分派
        if node is None or depth > 10:
            return None
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if value.endswith('.test.ts'):
                return ('filelit', value)
            if value == 'EVIDENCE_INPUTS_PATH':
                return ('output', 'ts-inputs.jsonl')
            if value.endswith(('.json', '.jsonl')):
                found = self.existing(value)
                return ('file', found) if found else ('literal', value)
            return ('literal', value)
        if isinstance(node, ast.Name):
            name = node.id
            if name == 'TASK':
                return ('task',)
            if name == 'replay':
                return ('replay',)
            if name == 'plan':
                return ('plan',)
            if name == 'plan_folder':
                return ('plan',)
            if name in ('prefix', 'group'):
                return ('prefix',)
            if name == 'variant':
                return ('variant',)
            if name == 'name':
                return ('local',)
            if name == 'random_replay':
                found = self.existing('random.json')
                return ('file', found) if found else None
            if name in self.vars:
                return self.eval(self.vars[name], depth + 1)
            # 驱动函数参数约定：folder／evidence 是本轮输出目录，plan_folder 是计划目录。
            if name in ('folder', 'evidence', 'output_dir', 'destination'):
                return ('run_dir',)
            if name in ('plan_folder', 'plan_dir'):
                return ('plan',)
            return None
        if isinstance(node, ast.Attribute):
            if node.attr == 'resolve':
                return self.eval(node.value, depth + 1)
            if node.attr == 'parent':
                base = self.eval(node.value, depth + 1)
                if base in (('replay',), ('plan',)):
                    return ('plan_dir',)
                if base and base[0] in ('run_dir', 'output'):
                    return ('run_dir',)
                return None
            if node.attr == 'replay':
                return ('replay',)
            if node.attr in ('plan', 'plan_folder'):
                return ('plan',)
            if node.attr == 'side':
                # 全量运行的 TS 分派只跑 ts 分支。
                return ('literal', 'ts')
            if node.attr == 'variant':
                return ('variant',)
            if node.attr in ('group', 'kind', 'variant_name'):
                return ('prefix',)
            if node.attr in ('raw', 'output', 'directory', 'out', 'folder', 'target', 'dest',
                             'destination', 'work') or node.attr.endswith(('_raw', '_dir')):
                return ('output', node.attr)
            if node.attr == 'report':
                return ('run_dir',)
            if node.attr == 'environ':
                return ('passthrough',)
            return None
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in ('str', 'Path'):
                return self.eval(node.args[0], depth + 1) if node.args else None
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'resolve':
                return self.eval(node.func.value, depth + 1)
            return None
        if isinstance(node, ast.BinOp):
            left, right = self.eval(node.left, depth + 1), self.eval(node.right, depth + 1)
            if isinstance(node.op, ast.Div):
                if right and right[0] == 'file' and left in (('task',), ('plan_dir',), ('run_dir',), ('plan',)):
                    return right
                if left in (('task',), ('plan_dir',)) and right and right[0] in ('literal', 'filelit'):
                    base = TASK if left == ('task',) else self.plan_dir
                    return ('file', base / right[1])
                if left == ('plan',) and right and right[0] in ('literal', 'filelit'):
                    return ('file', self.plan_dir / right[1])
                if left == ('replay',) and right and right[0] in ('literal', 'filelit'):
                    return ('plan_dir',)
                if left == ('run_dir',) and right and right[0] in ('literal', 'filelit'):
                    return ('output', right[1])
                if left and left[0] == 'file' and right and right[0] in ('literal', 'filelit'):
                    return ('file', Path(left[1]) / right[1])
                if left and left[0] == 'output' and right:
                    return left
                return None
            if isinstance(node.op, ast.Add):
                if left == ('prefix',) and right and right[0] == 'literal' and self.prefix:
                    found = self.existing(self.prefix + right[1])
                    return ('file', found) if found else None
                if left and left[0] == 'literal' and right and right[0] == 'literal':
                    joined = left[1] + right[1]
                    found = self.existing(joined)
                    return ('file', found) if found else ('literal', joined)
                if left and left[0] == 'file' and right and right[0] == 'literal':
                    return ('file', Path(str(left[1]) + right[1]))
                return None
            return None
        if isinstance(node, ast.BoolOp):
            for value in node.values:
                result = self.eval(value, depth + 1)
                if result:
                    return result
            return None
        if isinstance(node, ast.Subscript):
            inner = self.eval(node.slice, depth + 1)
            is_environ = (isinstance(node.value, ast.Attribute) and node.value.attr == 'environ') \
                or (isinstance(node.value, ast.Name) and node.value.id in ('env', 'environment', 'os_environ'))
            if is_environ:
                if inner == ('output', 'ts-inputs.jsonl'):
                    return ('output', 'ts-inputs.jsonl')
                key = self.dynamic_key(node.slice)
                return ('envref', key) if key else ('passthrough',)
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
                return self.eval(node.value, depth + 1)
            return None
        if isinstance(node, ast.JoinedStr):
            parts = []
            for value in node.values:
                if isinstance(value, ast.Constant):
                    parts.append(str(value.value))
                elif isinstance(value, ast.FormattedValue):
                    inner = self.eval(value.value, depth + 1)
                    if inner and inner[0] in ('literal', 'filelit'):
                        parts.append(inner[1])
                    elif inner == ('variant',) and self.variant:
                        parts.append(self.variant)
                    elif inner == ('local',):
                        return ('local',)
                    else:
                        return None
                else:
                    return None
            return ('literal', ''.join(parts))
        return None

    def dynamic_key(self, node):
        """env[entry['ts_observations_env']] 这类动态键，按局部登记表换成真实环境变量名。"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) \
                and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            return self.dynamic_keys.get(node.slice.value)
        return None

    def classify(self, node):
        result = self.eval(node)
        if not result:
            return None, None
        kind = result[0]
        if kind == 'output':
            return 'output', result[1]
        if kind == 'local':
            return 'local', None
        if kind == 'variant':
            return ('value', self.variant) if self.variant else (None, None)
        if kind == 'prefix':
            return ('value', self.prefix) if self.prefix else (None, None)
        if kind == 'envref':
            return 'envref', result[1]
        if kind == 'passthrough':
            return 'passthrough', None
        if kind == 'file':
            return ('file', Path(result[1])) if Path(result[1]).is_file() else (None, None)
        if kind == 'plan_dir':
            return ('file', self.plan_dir) if self.plan_dir.is_dir() else (None, None)
        if kind == 'replay':
            candidate = self.replay
            if candidate is None:
                for name in ('replay.jsonl', 'replay-inputs.jsonl'):
                    candidate = self.existing(name)
                    if candidate:
                        break
            return ('file', Path(candidate)) if candidate and Path(candidate).is_file() else (None, None)
        if kind == 'plan':
            candidate = self.plan_dir / 'input-plan.json'
            return ('file', candidate) if candidate.is_file() else (None, None)
        return None, None


def env_assignments(resolver, dynamic_keys=None):
    """驱动里 env[...] / dict(os.environ, ...) / env.update(...) 的赋值节点。

    标准局部适配器用 env[entry['ts_observations_env']] 这类动态键，按局部登记表换成真实环境变量名。
    """
    rows = []
    dynamic_keys = dynamic_keys or {}

    def key_of(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) \
                and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            return dynamic_keys.get(node.slice.value)
        return None

    for node in ast.walk(resolver.tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) \
                        and target.value.id in ('env', 'environment', 'os_environ'):
                    name = key_of(target.slice)
                    if name:
                        rows.append((name, node.value))
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) \
                    and node.value.func.id == 'dict':
                rows.extend((kw.arg, kw.value) for kw in node.value.keywords if kw.arg)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == 'update' and isinstance(node.func.value, ast.Name) \
                and node.func.value.id in ('env', 'environment'):
            rows.extend((kw.arg, kw.value) for kw in node.keywords if kw.arg)
    return [(name, value) for name, value in rows if name.startswith('MIGRATION_')]


def driver_commands(path):
    """采集驱动里的探针、emit-ts argv、原文件与引用到的全部探针名。"""
    text = path.read_text(errors='replace')
    match = re.search(r"--setupFilesAfterEnv'?,\s*(.*?)'--json'", text, re.S)
    segment = match.group(1) if match else ''
    setup = []
    for name in re.findall(r'([A-Za-z0-9_.\-]+\.cjs)', segment):
        if name not in GLOBAL_SETUP and name not in setup:
            setup.append(name)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) \
                and node.value.value.endswith('.cjs'):
            if node.value.value not in GLOBAL_SETUP and node.value.value not in setup:
                setup.append(node.value.value)
    emit_nodes = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('run', 'check_output'):
            argv = list(node.args)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ('run', 'check_output') and isinstance(node.func.value, ast.Name) \
                and node.func.value.id == 'subprocess':
            argv = list(node.args[0].elts) if node.args and isinstance(node.args[0], (ast.List, ast.Tuple)) \
                else list(node.args)
        elif isinstance(node, (ast.List, ast.Tuple)):
            argv = list(node.elts)
        else:
            continue
        constants = [e.value for e in argv if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        if 'emit-ts' in constants:
            emit_nodes = argv
            break
    referenced = [name for name in re.findall(r'([A-Za-z0-9_.\-]+\.cjs)', text) if name not in GLOBAL_SETUP]
    source_files = sorted(set(re.findall(r'(src/[A-Za-z0-9_./\-]+\.test\.ts)', text)))
    return {'setup': setup, 'referenced': sorted(set(referenced)), 'emit': emit_nodes,
            'source_files': source_files, 'text': text}


def load_drivers():
    rows = []
    for path in sorted(set(TASK.glob('capture-*.py')) | set(TASK.glob('*-local-gate.py'))
                       | set(TASK.glob('*-evidence.py')) | set(TASK.glob('replay-*.py'))):
        try:
            commands = driver_commands(path)
        except SyntaxError:
            continue
        if commands['setup'] or commands['emit'] or commands['source_files'] or commands['referenced']:
            rows.append(dict(commands, path=path))
    return rows


def output_slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower().removeprefix('migration_')).strip('-')


def primary_env(outputs, module_entry):
    preferred = (module_entry or {}).get('ts_observations_env')
    if preferred and preferred in outputs:
        return preferred
    for suffix in ('_TS_OBSERVATIONS', '_OBSERVATIONS', '_TS_INPUTS', '_INPUTS', '_FRAMES', '_RAW'):
        for name in outputs:
            if name.endswith(suffix):
                return name
    return next(iter(outputs), None)


def emit_recipe(resolver, nodes, primary, outputs):
    """驱动里的 emit-ts argv → 可复用到全量运行的命令模板。"""
    slug_to_env = {slug: env for env, slug in outputs.items()}
    argv, unresolved = [], []
    for node in nodes:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if value == 'python3':
                argv.append('python3')
            elif value.endswith('.py'):
                argv.append(str(TASK / value) if (TASK / value).is_file() else value)
            else:
                argv.append(value)
            continue
        kind, value = resolver.classify(node)
        if kind == 'output':
            env = slug_to_env.get(value)
            if env is None:
                argv.append('{output}')
            elif env == primary:
                argv.append('{raw}')
            else:
                argv.append('{out:' + env + '}')
        elif kind == 'file':
            argv.append(str(value))
        elif kind == 'envref':
            argv.append('{raw}' if value == primary else '{out:' + value + '}')
        elif kind == 'passthrough':
            argv.append('{output}')
        elif kind == 'local':
            argv.append('{local}')
        elif kind in ('value', 'prefix', 'variant'):
            argv.append(value)
        else:
            unresolved.append(resolver.source(node))
    script = argv[1] if len(argv) > 1 and argv[1].endswith('.py') else None
    if unresolved or script is None:
        return {'script': None, 'argv': [], 'unresolved': unresolved}
    return {'script': script, 'argv': argv, 'unresolved': []}


def probe_plans(probe_name, probe_path, drivers, files, module_entry, plan_dir, replay, preferred=None):
    """为单个探针找齐输出／语料／取值环境变量；返回 (plan, 未解析原因)。"""
    needed = probe_envs(probe_path)
    if not needed:
        return {'driver': str(preferred['path'].relative_to(TASK)) if preferred else None,
                'outputs': {}, 'corpus': {}, 'values': {}}, []
    ordered = ([preferred] if preferred else []) + [
        row for row in drivers if (probe_name in row['referenced'] or probe_name in row['setup'])
        and row is not preferred]
    reasons = []
    for driver in ordered:
        resolver = Resolver(driver['path'], files[0] if len(files) == 1 else '', plan_dir, replay)
        resolver.dynamic_keys = dict(module_entry or {})
        table = {}
        for env, value in env_assignments(resolver, module_entry or {}):
            table.setdefault(env, resolver.classify(value))
        outputs = {env: value for env, (kind, value) in table.items() if kind == 'output' and env in needed}
        corpus = {env: value for env, (kind, value) in table.items() if kind == 'file' and env in needed}
        values = {env: value for env, (kind, value) in table.items() if kind == 'value' and env in needed}
        missing = sorted(env for env in needed
                         if env not in outputs and env not in corpus and env not in values
                         and env not in GLOBAL_ENVS)
        if not missing:
            plan = {'driver': str(driver['path'].relative_to(TASK)), 'outputs': outputs,
                    'corpus': {env: str(path) for env, path in corpus.items()}, 'values': values}
            if driver['emit']:
                plan['emit'] = emit_recipe(resolver, driver['emit'], None, outputs)
            return plan, []
        reasons.append(f"{driver['path'].name}: {','.join(missing)}")
    return None, reasons


def probe_owner(probe_name, names):
    """按最长局部名前缀判定探针归属：capture-<局部名>[-...].cjs。"""
    stem = probe_name[len('capture-'):-len('.cjs')] if probe_name.startswith('capture-') else probe_name
    owners = [name for name in names if stem == name or stem.startswith(name + '-')]
    return max(owners, key=len) if owners else None


def driver_for(drivers, capture):
    if not capture:
        return None
    return next((row for row in drivers if row['path'].name == capture), None)


def build_entry(item, locals_modules, catalog_files, drivers, all_probes, local_names):
    """把一个局部登记折算成探针条目；返回 (entry, problem)。"""
    name = item['name']
    plan_path = (TASK / item['input_plan']).resolve()
    module_entry = locals_modules.get(name)
    replay = (TASK / item['replay']).resolve() if item.get('replay') else None
    files = []
    if plan_path.is_file():
        ids = set(json.loads(plan_path.read_text()))
        files = sorted({catalog_files[identity] for identity in ids if identity in catalog_files})
    if module_entry:
        files = [module_entry['file']]
    if not files:
        return None, ('unresolved', '输入计划的 caseId 反查不到原文件')

    registered = TASK / item['capture'] if item.get('capture') else None
    registered_driver = driver_for(drivers, item.get('capture'))
    owned = [probe for probe in all_probes if probe_owner(probe, local_names) == name]
    plan_refs = [row for row in drivers
                 if plan_path.name in row['text'] or (plan_path.parent.name not in ('plan', 'plan2', 'plan-v2')
                                                      and plan_path.parent.name in row['text'])]
    file_refs = [row for row in drivers if set(files) & set(row['source_files'])]
    tiers = []
    if module_entry:
        tiers.append(('locals-module', [module_entry['probe']], registered_driver))
    if owned:
        tiers.append(('probe-name', owned, registered_driver))
    if registered_driver:
        tiers.append(('registered-capture', registered_driver['setup'] or registered_driver['referenced'],
                      registered_driver))
    if len(plan_refs) == 1:
        tiers.append(('plan-driver', plan_refs[0]['setup'] or plan_refs[0]['referenced'], plan_refs[0]))
    if len(file_refs) == 1:
        tiers.append(('file-driver', file_refs[0]['setup'] or file_refs[0]['referenced'], file_refs[0]))
    if not tiers:
        family = name.split('-')[0]
        for probe in all_probes:
            stem = probe[len('capture-'):-len('.cjs')]
            if not stem.startswith(family + '-'):
                continue
            owners = [row for row in drivers if probe in row['referenced'] or probe in row['setup']]
            if any(not row['source_files'] or set(files) & set(row['source_files']) for row in owners):
                tiers.append(('probe-family', [probe], owners[0] if len(owners) == 1 else None))
                break

    reasons = []
    for label, candidates, preferred in tiers:
        probe_rows = []
        for probe_name in dict.fromkeys(candidates):
            probe_path = TASK / probe_name
            if not probe_path.is_file():
                reasons.append(f'{probe_name}: 探针未落盘')
                continue
            declared = set(re.findall(r'(src/[A-Za-z0-9_./\-]+\.test\.ts)',
                                      probe_path.read_text(errors='replace')))
            if declared and not (declared & set(files)):
                reasons.append(f'{probe_name}: 探针声明的原文件不在本局部计划内')
                continue
            if len(files) > 1 and len(candidates) > 1 and not declared:
                reasons.append(f'{probe_name}: 多原文件多探针，无法唯一确定对应关系')
                continue
            plan, missing = probe_plans(probe_name, probe_path, drivers, files, module_entry,
                                        plan_path.parent, replay, preferred)
            mode = 'direct' if probe_direct(probe_path) else 'raw'
            if mode == 'raw':
                if not probe_envs(probe_path):
                    reasons.append(f'{probe_name}: 无输出环境变量')
                    continue
                if plan is None:
                    reasons.append(f'{probe_name}: 环境变量无法解析（' + '；'.join(missing) + '）')
                    continue
                if not plan['outputs']:
                    reasons.append(f'{probe_name}: 未确定原始轨迹输出环境变量')
                    continue
            row = {'local': name, 'probe': probe_name, 'mode': mode, 'tier': label}
            if plan:
                row['driver'] = plan['driver']
                if plan['outputs']:
                    row['outputs'] = plan['outputs']
                if plan['corpus']:
                    row['corpus'] = plan['corpus']
                if plan['values']:
                    row['values'] = plan['values']
                if mode == 'raw':
                    row['emit'] = plan.get('emit') or {'script': None, 'argv': [], 'unresolved': []}
            probe_rows.append(row)
        if probe_rows:
            output_envs = {}
            for row in probe_rows:
                output_envs.update(row.get('outputs', {}))
            primary = primary_env(output_envs, module_entry)
            outputs = {}
            for env in output_envs:
                outputs[env] = f'{name}.calls.raw.jsonl' if env == primary \
                    else f'{name}.{output_slug(env)}.raw.jsonl'
            for row in probe_rows:
                row['env'] = primary if row['mode'] == 'raw' else None
                row['raw'] = outputs.get(primary) if row['mode'] == 'raw' else None
                row['outputs'] = {env: outputs[env] for env in row.get('outputs', {})}
                if row['mode'] == 'raw' and row.get('emit', {}).get('argv'):
                    row['emit']['argv'] = list(row['emit']['argv'])
            inputs_envs = {env for env in output_envs if env.endswith('_TS_INPUTS')}
            for driver in [registered_driver] + plan_refs + file_refs:
                if driver:
                    for env, value in env_assignments(
                            Resolver(driver['path'], files[0] if len(files) == 1 else '',
                                     plan_path.parent, replay), module_entry or {}):
                        if env.endswith('_TS_INPUTS'):
                            inputs_envs.add(env)
            entry = {
                'local': name, 'capture': item.get('capture'), 'files': files, 'plan': str(plan_path),
                'tier': label, 'probes': probe_rows, 'outputs': outputs,
                'inputs_envs': sorted(inputs_envs | ({(module_entry or {}).get('inputs_env')}
                                                     if (module_entry or {}).get('inputs_env') else set())),
                'inputs_env': (module_entry or {}).get('inputs_env') or (sorted(inputs_envs)[0]
                                                                        if inputs_envs else None),
                'probe': probe_rows[0]['probe'], 'env': probe_rows[0]['env'],
            }
            if reasons:
                entry['notes'] = reasons
            return entry, None
    return None, ('unresolved', '；'.join(reasons) or '没有可用探针')


def canonicalize(locals_out):
    """同一（探针，环境变量）在全量运行里只装一次、只写一个轨迹文件；名字取排序后第一个局部。"""
    canonical, owners = {}, {}
    for name in sorted(locals_out):
        entry = locals_out[name]
        for probe in entry['probes']:
            for env in probe.get('outputs', {}):
                canonical.setdefault((probe['probe'], env), f'{name}.calls.raw.jsonl' if env == probe['env']
                                     else f'{name}.{output_slug(env)}.raw.jsonl')
                owners.setdefault((probe['probe'], env), name)
    for name, entry in locals_out.items():
        for probe in entry['probes']:
            if probe['mode'] != 'raw':
                continue
            primary_raw = None
            for env in list(probe.get('outputs', {})):
                target = canonical[(probe['probe'], env)]
                probe['outputs'][env] = target
                if env == probe['env']:
                    primary_raw = target
            probe['raw'] = primary_raw
            if primary_raw:
                probe['rawOwner'] = owners[(probe['probe'], probe['env'])]
            argv = probe.get('emit', {}).get('argv')
            if argv:
                def substitute(part):
                    if part == '{raw}':
                        return '{runDir}/' + primary_raw if primary_raw else part
                    if part.startswith('{out:') and part.endswith('}'):
                        name = canonical.get((probe['probe'], part[5:-1]))
                        return '{runDir}/' + name if name else part
                    return part
                probe['emit']['argv'] = [substitute(part) for part in argv]
    for name, entry in locals_out.items():
        entry['probe'] = entry['probes'][0]['probe']
        entry['env'] = entry['probes'][0]['env']
    return canonical


def write_full_run(config_path, ts_reports, java_reports):
    """把 fullRun 段写进 full-evidence-locals.json；整体读改写都在 flock 内（与 register-local.py 同锁）。"""
    entry = {
        'tsCommand': ['python3', 'run-full-ts-capture.py', '--run-dir', '{runDir}',
                      '--report', ts_reports[0]],
        # 尾部的 clean test 是固定阶段声明：evidence-bundle capture 与 preflight 都要求
        # 最终 Java 命令自身含无过滤的 clean test；脚本内部始终按无过滤 clean test 执行。
        'javaCommand': ['python3', 'run-full-java-capture.py', '--run-dir', '{runDir}',
                        '--reports', *java_reports, 'clean', 'test'],
        'tsReports': list(ts_reports),
        'javaReports': list(java_reports),
    }
    with open(LOCK, 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            data = json.loads(Path(config_path).read_text())
            previous = data.get('fullRun')
            data['fullRun'] = entry
            Path(config_path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
    return entry, previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=CONFIG)
    parser.add_argument('--catalog', type=Path, default=CATALOG)
    parser.add_argument('--output', type=Path, default=TASK / 'full-run-probes.json')
    parser.add_argument('--quiet', action='store_true', help='只打印汇总，不逐条打印 unresolved')
    parser.add_argument('--skip-full-run', action='store_true', help='不写 full-evidence-locals.json 的 fullRun 段')
    options = parser.parse_args()

    config = read_locked(options.config)
    catalog = json.loads(options.catalog.read_text())
    catalog_files = {case['id']: file['path'] for file in catalog['files'] for case in file['cases']}
    locals_modules, module_names = load_locals_modules()
    drivers = load_drivers()
    all_probes = sorted(path.name for path in TASK.glob('capture-*.cjs'))
    local_names = [item['name'] for item in config['locals']]

    files, envs, locals_out, unresolved, pending = {}, {}, {}, [], []
    for item in sorted(config['locals'], key=lambda row: row['name']):
        entry, problem = build_entry(item, locals_modules, catalog_files, drivers,
                                     all_probes, local_names)
        if problem:
            kind, detail = problem
            record = {'local': item['name'], 'capture': item.get('capture'),
                      'inputPlan': item['input_plan'], 'reason': detail}
            (pending if kind == 'pending' else unresolved).append(record)
            continue
        locals_out[entry['local']] = entry
        for env in entry['inputs_envs']:
            envs[env] = entry['local']
        for path in entry['files']:
            row = files.setdefault(path, {'probes': []})
            for probe in entry['probes']:
                if probe not in row['probes']:
                    row['probes'].append(probe)
            row['probe'] = row['probes'][0]['probe']
            row['env'] = row['probes'][0]['env']
    canonical = canonicalize(locals_out)
    files = {}
    for entry in locals_out.values():
        for path in entry['files']:
            row = files.setdefault(path, {'probes': []})
            for probe in entry['probes']:
                if not any(existing['probe'] == probe['probe'] for existing in row['probes']):
                    row['probes'].append(probe)
            row['probe'] = row['probes'][0]['probe']
            row['env'] = row['probes'][0]['env']
    mapped = set(files)
    uncovered = sorted(path for path in (file['path'] for file in catalog['files']) if path not in mapped)
    result = {
        'schemaVersion': 1, 'producer': 'build-full-run-probes.py', 'localsModules': module_names,
        'locals': locals_out, 'files': files, 'envs': envs,
        'pending': pending, 'unresolved': unresolved, 'unmappedCatalogFiles': uncovered,
    }
    options.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    full_run = None
    if not options.skip_full_run:
        full_run, _ = write_full_run(options.config, ['ts-jest.json'], ['java-surefire.xml'])
    print(json.dumps({'locals': len(locals_out), 'files': len(files), 'probes': sum(len(row['probes']) for row in files.values()),
                      'envs': len(envs), 'pending': len(pending), 'unresolved': len(unresolved),
                      'unmappedCatalogFiles': len(uncovered),
                      'fullRun': bool(full_run)}, ensure_ascii=False))
    if not options.quiet:
        for record in pending:
            print('PENDING ' + json.dumps(record, ensure_ascii=False))
        for record in unresolved:
            print('UNRESOLVED ' + json.dumps(record, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
