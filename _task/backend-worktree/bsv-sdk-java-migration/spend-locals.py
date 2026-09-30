#!/usr/bin/env python3
"""script/spend 批待采集原测试文件的登记表：原文件、Java 测试类、探针与环境变量。

与 `script-locals.py` 的差别：同一原文件可能被多个 Java 类覆盖（如 Spend.test.ts 的
有效向量与 SpendCoreTest），因此这里的局部按 **Java 类** 而不是按文件划分，冻结与
采集工具会把清单裁剪到本类名下的用例。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'spend-additional': {
        'file': 'src/script/__tests/Spend.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.script.SpendAdditionalTest',
        'test': 'SpendAdditionalTest',
        'probe': 'capture-spend-additional-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SPEND_ADDITIONAL_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SPEND_ADDITIONAL_TS_INPUTS',
    },
    'spend-core': {
        'file': 'src/script/__tests/Spend.test.ts',
        'java_class': 'com.metanet4j.bsv.script.SpendCoreTest',
        'test': 'SpendCoreTest',
        'probe': 'capture-spend-core-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SPEND_CORE_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SPEND_CORE_TS_INPUTS',
    },
    'spend-complex': {
        'file': 'src/script/__tests/SpendComplex.test.ts',
        'java_class': 'com.metanet4j.bsv.script.SpendComplexTest',
        'test': 'SpendComplexTest',
        'probe': 'capture-spend-complex-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SPEND_COMPLEX_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SPEND_COMPLEX_TS_INPUTS',
    },
    'spend-codeseparator': {
        'file': 'src/script/__tests/Spend.codeseparator.test.ts',
        'java_class': 'com.metanet4j.bsv.script.SpendCodeSeparatorTest',
        'test': 'SpendCodeSeparatorTest',
        'probe': 'capture-spend-codeseparator-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SPEND_CODESEPARATOR_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SPEND_CODESEPARATOR_TS_INPUTS',
    },
    'normative-vectors': {
        'file': 'src/script/__tests/NormativeVectors.test.ts',
        'java_class': 'com.metanet4j.bsv.script.NormativeVectorsTest',
        'test': 'NormativeVectorsTest',
        'probe': 'capture-spend-normative-vectors-inputs.cjs',
        'ts_observations_env': 'MIGRATION_NORMATIVE_VECTORS_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_NORMATIVE_VECTORS_TS_INPUTS',
    },
    'spend-verifier': {
        'file': 'src/script/__tests/Spend.verifier.test.ts',
        'java_class': 'com.metanet4j.bsv.script.SpendVerifierTest',
        'test': 'SpendVerifierTest',
        'probe': 'capture-spend-verifier-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SPEND_VERIFIER_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SPEND_VERIFIER_TS_INPUTS',
    },
    'lrshiftnum': {
        'file': 'src/script/__tests/lrshiftnum.test.ts',
        'java_class': 'com.metanet4j.bsv.script.LrShiftNumTest',
        'test': 'LrShiftNumTest',
        'probe': 'capture-spend-lrshiftnum-inputs.cjs',
        'ts_observations_env': 'MIGRATION_LRSHIFTNUM_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_LRSHIFTNUM_TS_INPUTS',
    },
    'chronicle': {
        'file': 'src/script/__tests/Chronicle.test.ts',
        'java_class': 'com.metanet4j.bsv.script.ChronicleTest',
        'test': 'ChronicleTest',
        'probe': 'capture-spend-chronicle-inputs.cjs',
        'ts_observations_env': 'MIGRATION_CHRONICLE_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_CHRONICLE_TS_INPUTS',
    },
    'spend-chronicle-vector': {
        'file': 'src/script/__tests/SpendValildVectors.test.ts',
        'java_class': 'com.metanet4j.bsv.script.SpendChronicleVectorTest',
        'test': 'SpendChronicleVectorTest',
        'probe': 'capture-spend-chronicle-vector-inputs.cjs',
        'ts_observations_env': 'MIGRATION_SPEND_CHRONICLE_VECTOR_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_SPEND_CHRONICLE_VECTOR_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记 spend 局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
