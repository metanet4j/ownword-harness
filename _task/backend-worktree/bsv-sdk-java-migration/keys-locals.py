#!/usr/bin/env python3
"""keys 待采集原测试文件的登记表：原文件、Java 测试类、探针与环境变量。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'public-key': {
        'file': 'src/primitives/__tests/PublicKey.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.PublicKeyTest',
        'test': 'PublicKeyTest',
        'probe': 'capture-public-key-inputs.cjs',
        'ts_observations_env': 'MIGRATION_PUBLIC_KEY_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_PUBLIC_KEY_TS_INPUTS',
    },
    'public-key-additional': {
        'file': 'src/primitives/__tests/PublicKey.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.PublicKeyAdditionalTest',
        'test': 'PublicKeyAdditionalTest',
        'probe': 'capture-public-key-additional-inputs.cjs',
        'ts_observations_env': 'MIGRATION_PUBLIC_KEY_ADDITIONAL_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_PUBLIC_KEY_ADDITIONAL_TS_INPUTS',
    },
    'ecdsa': {
        'file': 'src/primitives/__tests/ECDSA.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.ECDSATest',
        'test': 'ECDSATest',
        'probe': 'capture-ecdsa-inputs.cjs',
        'ts_observations_env': 'MIGRATION_ECDSA_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_ECDSA_TS_INPUTS',
    },
    'schnorr': {
        'file': 'src/primitives/__tests/Schnorr.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.SchnorrTest',
        'test': 'SchnorrTest',
        'probe': 'capture-schnorr-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SCHNORR_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SCHNORR_TS_INPUTS',
    },
    'symmetric-key': {
        'file': 'src/primitives/__tests/SymmetricKey.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.SymmetricKeyTest',
        'test': 'SymmetricKeyTest',
        'probe': 'capture-symmetric-key-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SYMMETRIC_KEY_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SYMMETRIC_KEY_TS_INPUTS',
    },
    'ecies': {
        'file': 'src/compat/__tests/ECIES.test.ts',
        'java_class': 'com.metanet4j.bsv.compat.ECIESTest',
        'test': 'ECIESTest',
        'probe': 'capture-ecies-inputs.cjs',
        'ts_observations_env': 'MIGRATION_ECIES_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_ECIES_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记 keys 局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
