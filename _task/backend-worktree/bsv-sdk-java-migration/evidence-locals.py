#!/usr/bin/env python3
"""结构覆盖率补强局部的登记表：原文件、Java 测试类、探针与环境变量。

只登记本轮三个全新文件局部（HD／Script／Hash）；逻辑与 transaction-locals.py 一致，
便于 prepare-evidence-local.py 与 capture-evidence-local.py 共用同一套约定。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'hd': {
        'file': 'src/compat/__tests/HD.test.ts',
        'java_class': 'com.metanet4j.bsv.compat.HDTest',
        'test': 'HDTest',
        'probe': 'capture-hd-inputs.cjs',
        'ts_observations_env': 'MIGRATION_HD_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_HD_TS_INPUTS',
    },
    'script': {
        'file': 'src/script/__tests/Script.test.ts',
        'java_class': 'com.metanet4j.bsv.script.ScriptTest',
        'test': 'ScriptTest',
        'probe': 'capture-script-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SCRIPT_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SCRIPT_TS_INPUTS',
    },
    'hash': {
        'file': 'src/primitives/__tests/Hash.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.HashTest',
        'test': 'HashTest',
        'probe': 'capture-hash-inputs.cjs',
        'ts_observations_env': 'MIGRATION_HASH_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_HASH_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记结构补强局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
