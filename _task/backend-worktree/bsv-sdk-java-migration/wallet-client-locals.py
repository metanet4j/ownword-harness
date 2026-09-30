#!/usr/bin/env python3
"""wallet-client 待采集原测试文件的登记表：原文件、Java 测试类、探针与环境变量。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'wallet-client': {
        'file': 'src/wallet/__tests/WalletClient.test.ts',
        'java_class': 'com.metanet4j.bsv.wallet.WalletClientTest',
        'test': 'WalletClientTest',
        'probe': 'capture-wallet-client-inputs.cjs',
        'ts_observations_env': 'MIGRATION_WALLET_CLIENT_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_WALLET_CLIENT_TS_INPUTS',
    },
    'wallet-client-additional': {
        'file': 'src/wallet/__tests/WalletClient.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.wallet.WalletClientAdditionalTest',
        'test': 'WalletClientAdditionalTest',
        'probe': 'capture-wallet-client-additional-inputs.cjs',
        'ts_observations_env': 'MIGRATION_WALLET_CLIENT_ADDITIONAL_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_WALLET_CLIENT_ADDITIONAL_TS_INPUTS',
    },
    'wallet-client-substrate': {
        'file': 'src/wallet/__tests/WalletClient.substrate.test.ts',
        'java_class': 'com.metanet4j.bsv.wallet.WalletClientSubstrateTest',
        'test': 'WalletClientSubstrateTest',
        'probe': 'capture-wallet-client-substrate-inputs.cjs',
        'ts_observations_env': 'MIGRATION_WALLET_CLIENT_SUBSTRATE_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_WALLET_CLIENT_SUBSTRATE_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记钱包客户端局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
