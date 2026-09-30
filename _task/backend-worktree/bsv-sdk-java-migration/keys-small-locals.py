#!/usr/bin/env python3
"""keys 小文件批次的登记表：原文件、Java 测试类、探针与环境变量。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'ecdsa-additional': {
        'file': 'src/primitives/__tests/ECDSA.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.ECDSAAdditionalTest',
        'test': 'ECDSAAdditionalTest',
        'probe': 'capture-ecdsa-additional-inputs.cjs',
        'ts_observations_env': 'MIGRATION_ECDSA_ADDITIONAL_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_ECDSA_ADDITIONAL_TS_INPUTS',
    },
    'ecdh': {
        'file': 'src/primitives/__tests/ECDH.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.ECDHTest',
        'test': 'ECDHTest',
        'probe': 'capture-ecdh-inputs.cjs',
        'ts_observations_env': 'MIGRATION_ECDH_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_ECDH_TS_INPUTS',
    },
    'secp256r1': {
        'file': 'src/primitives/__tests/Secp256r1.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.Secp256r1Test',
        'test': 'Secp256r1Test',
        'probe': 'capture-secp256r1-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SECP256R1_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SECP256R1_TS_INPUTS',
    },
    'bug-31': {
        'file': 'src/primitives/__tests/bug-31.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.Bug31Test',
        'test': 'Bug31Test',
        'probe': 'capture-bug-31-inputs.cjs',
        'ts_observations_env': 'MIGRATION_BUG_31_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_BUG_31_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记 keys 小文件局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
