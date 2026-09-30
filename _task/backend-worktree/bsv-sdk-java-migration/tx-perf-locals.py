#!/usr/bin/env python3
"""transaction-performance 待采集原测试文件的登记表：原文件、Java 测试类、探针与环境变量。

Transaction.performance.test.ts 与 transaction-base 的其他交易局部共用同一 Java 包，
但登记表独立，避免与其他子代理的登记表互相改写。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'transaction-performance': {
        'file': 'src/transaction/__tests/Transaction.performance.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.TransactionPerformanceTest',
        'test': 'TransactionPerformanceTest',
        'probe': 'capture-transaction-performance-inputs.cjs',
        'ts_observations_env': 'MIGRATION_TRANSACTION_PERFORMANCE_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_TRANSACTION_PERFORMANCE_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记交易性能局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
