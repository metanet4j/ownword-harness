#!/usr/bin/env python3
"""script 批待采集原测试文件的登记表：原文件、Java 测试类、探针与环境变量。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'p2pkh-async-backend': {
        'file': 'src/script/templates/__tests/P2PKH.async-backend.test.ts',
        'java_class': 'com.metanet4j.bsv.script.templates.P2PKHAsyncBackendTest',
        'test': 'P2PKHAsyncBackendTest',
        'probe': 'capture-p2pkh-async-backend-inputs.cjs',
        'ts_observations_env': 'MIGRATION_P2PKH_ASYNC_BACKEND_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_P2PKH_ASYNC_BACKEND_TS_INPUTS',
    },
    'push-drop': {
        'file': 'src/script/templates/__tests/PushDrop.test.ts',
        'java_class': 'com.metanet4j.bsv.script.templates.PushDropTest',
        'test': 'PushDropTest',
        'probe': 'capture-push-drop-inputs.cjs',
        'ts_observations_env': 'MIGRATION_PUSH_DROP_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_PUSH_DROP_TS_INPUTS',
    },
    'r-puzzle': {
        'file': 'src/script/templates/__tests/RPuzzle.test.ts',
        'java_class': 'com.metanet4j.bsv.script.templates.RPuzzleTest',
        'test': 'RPuzzleTest',
        'probe': 'capture-r-puzzle-inputs.cjs',
        'ts_observations_env': 'MIGRATION_R_PUZZLE_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_R_PUZZLE_TS_INPUTS',
    },
    'transaction-verifier': {
        'file': 'src/transaction/__tests/Transaction.verifier.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.TransactionVerifierTest',
        'test': 'TransactionVerifierTest',
        'probe': 'capture-transaction-verifier-inputs.cjs',
        'ts_observations_env': 'MIGRATION_TRANSACTION_VERIFIER_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_TRANSACTION_VERIFIER_TS_INPUTS',
    },
    'transaction-evidence': {
        'file': 'src/transaction/__tests/TransactionEvidence.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.TransactionEvidenceTest',
        'test': 'TransactionEvidenceTest',
        'probe': 'capture-transaction-evidence-inputs.cjs',
        'ts_observations_env': 'MIGRATION_TRANSACTION_EVIDENCE_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_TRANSACTION_EVIDENCE_TS_INPUTS',
    },
    'transaction-evidence-coordinator': {
        'file': 'src/transaction/__tests/TransactionEvidenceCoordinator.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.TransactionEvidenceCoordinatorTest',
        'test': 'TransactionEvidenceCoordinatorTest',
        'probe': 'capture-transaction-evidence-coordinator-inputs.cjs',
        'ts_observations_env': 'MIGRATION_TRANSACTION_EVIDENCE_COORDINATOR_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_TRANSACTION_EVIDENCE_COORDINATOR_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记 script 局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
