#!/usr/bin/env python3
"""primitives 最后两个未计划原测试文件的登记表：原文件、Java 测试类、探针与环境变量。

与 transaction-locals.py 同一结构，只登记本批次（primitives-last）负责的两个文件：

- `aesgcm-man`：原用例分配 2^29+16 字节明文，单次 TS 运行约 66 分钟；探针把大数组
  记成「长度 + SHA-256」（与既有 symmetric-manual 摘要口径一致），逐字节循环仍由原
  测试执行。
- `async-crypto-backend`：`audit-tests.py` 已有固定语义规则 `async-ready-null-adapter-v1`
  （站点 38:7／42:7 必须保留原 `toBeUndefined` matcher、TS 实际 `undefined`、Java 实际
  `null`、期望 `[]` 且带 `pass`），探针按原观察形状记录，不简化。
"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
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
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记 primitives-last 局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
