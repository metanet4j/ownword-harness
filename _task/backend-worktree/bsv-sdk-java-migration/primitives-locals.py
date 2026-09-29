#!/usr/bin/env python3
"""primitives 待采集原测试文件的登记表：原文件、Java 测试类、探针与环境变量。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'signature': {
        'file': 'src/primitives/__tests/Signature.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.SignatureTest',
        'test': 'SignatureTest',
        'probe': 'capture-signature-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SIGNATURE_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SIGNATURE_TS_INPUTS',
    },
    'aesgcm': {
        'file': 'src/primitives/__tests/AESGCM.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.AESGCMTest',
        'test': 'AESGCMTest',
        'probe': 'capture-aesgcm-inputs.cjs',
        'ts_observations_env': 'MIGRATION_AESGCM_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_AESGCM_TS_INPUTS',
    },
    'reduction-context': {
        'file': 'src/primitives/__tests/ReductionContext.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.ReductionContextTest',
        'test': 'ReductionContextTest',
        'probe': 'capture-reduction-context-inputs.cjs',
        'ts_observations_env': 'MIGRATION_REDUCTION_CONTEXT_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_REDUCTION_CONTEXT_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记 primitives 局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
