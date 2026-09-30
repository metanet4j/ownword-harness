#!/usr/bin/env python3
"""结构覆盖率缺口待采集原测试文件的登记表：原文件、Java 测试类、探针与环境变量。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'chronicle-opcodes': {
        'file': 'src/script/__tests/ChronicleOpcodes.test.ts',
        'java_class': 'com.metanet4j.bsv.script.ChronicleOpcodesTest',
        'test': 'ChronicleOpcodesTest',
        'probe': 'capture-chronicle-opcodes-inputs.cjs',
        'ts_observations_env': 'MIGRATION_CHRONICLE_OPCODES_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_CHRONICLE_OPCODES_TS_INPUTS',
    },
    'simplified-fetch-transport-additional': {
        'file': 'src/auth/transports/__tests__/SimplifiedFetchTransport.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.transports.SimplifiedFetchTransportAdditionalTest',
        'test': 'SimplifiedFetchTransportAdditionalTest',
        'probe': 'capture-simplified-fetch-transport-additional-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SIMPLIFIED_FETCH_TRANSPORT_ADDITIONAL_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SIMPLIFIED_FETCH_TRANSPORT_ADDITIONAL_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记缺口局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
