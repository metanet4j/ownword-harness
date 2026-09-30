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
        # 该用例用 jest.spyOn(JSON, 'parse') 让解析抛字符串（非 Error），send 的结局文本无法在
        # Java 复现（Java 异常必有 Throwable 原因）；只冻结构造入口，原断言的消息语义仍由同一
        # 生产格式化入口逐站点比较。登记必须精确命中样本编号，否则本轮冻结直接报错。
        'unmirrorable_samples': {
            '483145e1fb0e24c53972c4393d4a163b946d1aece9e7f768850c2c8fcf84d684': ['send-02'],
        },
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记缺口局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
