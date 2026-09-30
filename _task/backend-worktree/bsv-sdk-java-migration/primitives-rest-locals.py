#!/usr/bin/env python3
"""primitives 剩余待采集原测试文件的登记表：原文件、Java 测试类、探针与环境变量。

与 transaction-locals.py 同一结构，只登记本批次（primitives-rest）负责的原文件。
"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'private-key': {
        'file': 'src/primitives/__tests/PrivateKey.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.PrivateKeyTest',
        'test': 'PrivateKeyTest',
        'probe': 'capture-private-key-inputs.cjs',
        'ts_observations_env': 'MIGRATION_PRIVATE_KEY_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_PRIVATE_KEY_TS_INPUTS',
    },
    'private-key-split': {
        'file': 'src/primitives/__tests/PrivateKey.split.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.PrivateKeySplitTest',
        'test': 'PrivateKeySplitTest',
        'probe': 'capture-private-key-split-inputs.cjs',
        'ts_observations_env': 'MIGRATION_PRIVATE_KEY_SPLIT_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_PRIVATE_KEY_SPLIT_TS_INPUTS',
    },
    'random': {
        'file': 'src/primitives/__tests/Random.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.RandomTest',
        'test': 'RandomTest',
        'probe': 'capture-random-inputs.cjs',
        # 固定语义规则 random-length-v1 要求长度断言保留原始字节数组。
        'ts_parity': 'capture-parity-array-length.cjs',
        'ts_observations_env': 'MIGRATION_RANDOM_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_RANDOM_TS_INPUTS',
    },
    'random-additional': {
        'file': 'src/primitives/__tests/Random.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.RandomAdditionalTest',
        'test': 'RandomAdditionalTest',
        'probe': 'capture-random-additional-inputs.cjs',
        # 固定语义规则 random-length-v1 要求长度断言保留原始字节数组。
        'ts_parity': 'capture-parity-array-length.cjs',
        'ts_observations_env': 'MIGRATION_RANDOM_ADDITIONAL_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_RANDOM_ADDITIONAL_TS_INPUTS',
    },
    'hash-additional': {
        'file': 'src/primitives/__tests/Hash.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.HashAdditionalTest',
        'test': 'HashAdditionalTest',
        'probe': 'capture-hash-additional-inputs.cjs',
        'ts_observations_env': 'MIGRATION_HASH_ADDITIONAL_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_HASH_ADDITIONAL_TS_INPUTS',
    },
    'aesgcm-man': {
        'file': 'src/primitives/__tests/AESGCM.man.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.AESGCMManualTest',
        'test': 'AESGCMManualTest',
        'probe': 'capture-aesgcm-man-inputs.cjs',
        'ts_observations_env': 'MIGRATION_AESGCM_MAN_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_AESGCM_MAN_TS_INPUTS',
    },
    'async-crypto-backend': {
        'file': 'src/primitives/__tests/AsyncCryptoBackend.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.AsyncCryptoBackendTest',
        'test': 'AsyncCryptoBackendTest',
        'probe': 'capture-async-crypto-backend-inputs.cjs',
        'ts_observations_env': 'MIGRATION_ASYNC_CRYPTO_BACKEND_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_ASYNC_CRYPTO_BACKEND_TS_INPUTS',
    },
    'symmetric-key-compatibility': {
        'file': 'src/primitives/__tests/SymmetricKeyCompatibility.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.SymmetricKeyCompatibilityTest',
        'test': 'SymmetricKeyCompatibilityTest',
        'probe': 'capture-symmetric-key-compatibility-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SYMMETRIC_KEY_COMPATIBILITY_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SYMMETRIC_KEY_COMPATIBILITY_TS_INPUTS',
    },
    'bignumber-dh-group': {
        'file': 'src/primitives/__tests/BigNumber.dhGroup.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.BigNumberDhGroupTest',
        'test': 'BigNumberDhGroupTest',
        'probe': 'capture-bignumber-dh-group-inputs.cjs',
        'ts_observations_env': 'MIGRATION_BIGNUMBER_DH_GROUP_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_BIGNUMBER_DH_GROUP_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记 primitives-rest 局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
