#!/usr/bin/env python3
"""transaction-base 待采集原测试文件的登记表：原文件、Java 测试类、探针与环境变量。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'transaction-ef-cache': {
        'file': 'src/transaction/__tests/Transaction.ef-cache.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.TransactionEfCacheTest',
        'test': 'TransactionEfCacheTest',
        'probe': 'capture-transaction-ef-cache-inputs.cjs',
        'ts_observations_env': 'MIGRATION_TRANSACTION_EF_CACHE_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_TRANSACTION_EF_CACHE_TS_INPUTS',
    },
    'transaction-additional': {
        'file': 'src/transaction/__tests/Transaction.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.TransactionAdditionalTest',
        'test': 'TransactionAdditionalTest',
        'probe': 'capture-transaction-additional-inputs.cjs',
        'ts_observations_env': 'MIGRATION_TRANSACTION_ADDITIONAL_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_TRANSACTION_ADDITIONAL_TS_INPUTS',
    },
    'transaction-signature-additional': {
        'file': 'src/primitives/__tests/TransactionSignature.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.TransactionSignatureAdditionalTest',
        'test': 'TransactionSignatureAdditionalTest',
        'probe': 'capture-transaction-signature-inputs.cjs',
        'ts_observations_env': 'MIGRATION_TRANSACTION_SIGNATURE_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_TRANSACTION_SIGNATURE_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记交易局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
