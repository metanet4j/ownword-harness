#!/usr/bin/env python3
"""misc 待采集原测试文件（script／http／primitives 杂项）的登记表：原文件、Java 测试类、探针与环境变量。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'locking-unlocking-script': {
        'file': 'src/script/__tests/LockingUnlockingScript.test.ts',
        'java_class': 'com.metanet4j.bsv.script.LockingUnlockingScriptTest',
        'test': 'LockingUnlockingScriptTest',
        'probe': 'capture-locking-unlocking-script-inputs.cjs',
        'ts_observations_env': 'MIGRATION_LOCKING_UNLOCKING_SCRIPT_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_LOCKING_UNLOCKING_SCRIPT_TS_INPUTS',
    },
    'script-additional': {
        'file': 'src/script/__tests/Script.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.script.ScriptAdditionalTest',
        'test': 'ScriptAdditionalTest',
        'probe': 'capture-script-additional-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SCRIPT_ADDITIONAL_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SCRIPT_ADDITIONAL_TS_INPUTS',
    },
    'binary-fetch-client': {
        'file': 'src/transaction/http/__tests/BinaryFetchClient.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.http.BinaryFetchClientTest',
        'test': 'BinaryFetchClientTest',
        'probe': 'capture-binary-fetch-client-inputs.cjs',
        'ts_observations_env': 'MIGRATION_BINARY_FETCH_CLIENT_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_BINARY_FETCH_CLIENT_TS_INPUTS',
    },
    'bignumber-additional': {
        'file': 'src/primitives/__tests/BigNumber.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.BigNumberAdditionalTest',
        'test': 'BigNumberAdditionalTest',
        'probe': 'capture-bignumber-additional-inputs.cjs',
        'ts_observations_env': 'MIGRATION_BIGNUMBER_ADDITIONAL_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_BIGNUMBER_ADDITIONAL_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记 misc 局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
