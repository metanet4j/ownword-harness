#!/usr/bin/env python3
"""transaction 待采集原测试文件的登记表：原文件、Java 测试类、探针与环境变量。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    # Transaction.test.ts 的 61 例（非向量部分）按 test-map.json 分散在 8 个既有 Java 类；
    # 同文件的 659 条向量用例属 transaction-shared-vectors 专用局部，不进本局部。
    'transaction': {
        'file': 'src/transaction/__tests/Transaction.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.TransactionCompleteBasicsTest',
        'java_classes': [
            'com.metanet4j.bsv.transaction.TransactionCompleteBasicsTest',
            'com.metanet4j.bsv.transaction.TransactionCompleteBeefTest',
            'com.metanet4j.bsv.transaction.TransactionCompleteBroadcastTest',
            'com.metanet4j.bsv.transaction.TransactionCompleteFeeTest',
            'com.metanet4j.bsv.transaction.TransactionCompletePreimageTest',
            'com.metanet4j.bsv.transaction.TransactionCompleteSigningTest',
            'com.metanet4j.bsv.transaction.TransactionCompleteVerificationTest',
            'com.metanet4j.bsv.transaction.TransactionCompleteWalletTest',
        ],
        'test': ','.join([
            'TransactionCompleteBasicsTest', 'TransactionCompleteBeefTest',
            'TransactionCompleteBroadcastTest', 'TransactionCompleteFeeTest',
            'TransactionCompletePreimageTest', 'TransactionCompleteSigningTest',
            'TransactionCompleteVerificationTest', 'TransactionCompleteWalletTest',
        ]),
        'probe': 'capture-transaction-inputs.cjs',
        'ts_observations_env': 'MIGRATION_TRANSACTION_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_TRANSACTION_TS_INPUTS',
    },
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
    'beef': {
        'file': 'src/transaction/__tests/Beef.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.BeefTest',
        'test': 'BeefTest',
        'probe': 'capture-beef-inputs.cjs',
        'ts_observations_env': 'MIGRATION_BEEF_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_BEEF_TS_INPUTS',
    },
    'beef-party-additional': {
        'file': 'src/transaction/__tests/BeefParty.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.BeefPartyAdditionalTest',
        'test': 'BeefPartyAdditionalTest',
        'probe': 'capture-beef-party-additional-inputs.cjs',
        'ts_observations_env': 'MIGRATION_BEEF_PARTY_ADDITIONAL_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_BEEF_PARTY_ADDITIONAL_TS_INPUTS',
    },
    'merkle-path': {
        'file': 'src/transaction/__tests/MerklePath.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.MerklePathTest',
        'test': 'MerklePathTest',
        'probe': 'capture-merkle-path-inputs.cjs',
        'ts_observations_env': 'MIGRATION_MERKLE_PATH_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_MERKLE_PATH_TS_INPUTS',
    },
    'merkle-path-safe-offsets': {
        'file': 'src/transaction/__tests/MerklePath.safeOffsets.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.MerklePathSafeOffsetsTest',
        'test': 'MerklePathSafeOffsetsTest',
        'probe': 'capture-merkle-path-safe-offsets-inputs.cjs',
        'ts_observations_env': 'MIGRATION_MERKLE_PATH_SAFE_OFFSETS_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_MERKLE_PATH_SAFE_OFFSETS_TS_INPUTS',
    },
    'merkle-path-bench': {
        'file': 'src/transaction/__tests/MerklePath.bench.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.MerklePathBenchTest',
        'test': 'MerklePathBenchTest',
        'probe': 'capture-merkle-path-bench-inputs.cjs',
        'ts_observations_env': 'MIGRATION_MERKLE_PATH_BENCH_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_MERKLE_PATH_BENCH_TS_INPUTS',
    },
    'transaction-signature-additional': {
        'file': 'src/primitives/__tests/TransactionSignature.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.primitives.TransactionSignatureAdditionalTest',
        'test': 'TransactionSignatureAdditionalTest',
        'probe': 'capture-transaction-signature-inputs.cjs',
        'ts_observations_env': 'MIGRATION_TRANSACTION_SIGNATURE_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_TRANSACTION_SIGNATURE_TS_INPUTS',
    },
    'http-wallet-wire': {
        'file': 'src/wallet/substrates/__tests/HTTPWalletWire.test.ts',
        'java_class': 'com.metanet4j.bsv.wallet.substrates.HTTPWalletWireTest',
        'test': 'HTTPWalletWireTest',
        'probe': 'capture-http-wallet-wire-inputs.cjs',
        'ts_observations_env': 'MIGRATION_HTTP_WALLET_WIRE_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_HTTP_WALLET_WIRE_TS_INPUTS',
    },
    'window-cwi': {
        'file': 'src/wallet/substrates/__tests/window.CWI.test.ts',
        'java_class': 'com.metanet4j.bsv.wallet.substrates.WindowCWISubstrateTest',
        'test': 'WindowCWISubstrateTest',
        'probe': 'capture-window-cwi-inputs.cjs',
        'ts_observations_env': 'MIGRATION_WINDOW_CWI_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_WINDOW_CWI_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记交易局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
