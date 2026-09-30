#!/usr/bin/env python3
"""http-chain 待采集原测试文件的登记表：原文件、Java 测试类、探针与环境变量。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'block-headers-service': {
        'file': 'src/transaction/chaintrackers/__tests/BlockHeadersService.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.chaintrackers.BlockHeadersServiceTest',
        'test': 'BlockHeadersServiceTest',
        'probe': 'capture-block-headers-service-inputs.cjs',
        'ts_observations_env': 'MIGRATION_BLOCK_HEADERS_SERVICE_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_BLOCK_HEADERS_SERVICE_TS_INPUTS',
    },
    'whats-on-chain-additional': {
        'file': 'src/transaction/chaintrackers/__tests/WhatsOnChain.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.chaintrackers.WhatsOnChainAdditionalTest',
        'test': 'WhatsOnChainAdditionalTest',
        'probe': 'capture-whats-on-chain-additional-inputs.cjs',
        'ts_observations_env': 'MIGRATION_WHATS_ON_CHAIN_ADDITIONAL_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_WHATS_ON_CHAIN_ADDITIONAL_TS_INPUTS',
    },
    'whats-on-chain-chain-tracker': {
        'file': 'src/transaction/chaintrackers/__tests/WhatsOnChainChainTracker.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.chaintrackers.WhatsOnChainChainTrackerTest',
        'test': 'WhatsOnChainChainTrackerTest',
        'probe': 'capture-whats-on-chain-chain-tracker-inputs.cjs',
        'ts_observations_env': 'MIGRATION_WHATS_ON_CHAIN_CHAIN_TRACKER_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_WHATS_ON_CHAIN_CHAIN_TRACKER_TS_INPUTS',
    },
    'default-http-client': {
        'file': 'src/transaction/http/__tests/DefaultHttpClient.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.http.DefaultHttpClientTest',
        'test': 'DefaultHttpClientTest',
        'probe': 'capture-default-http-client-inputs.cjs',
        'ts_observations_env': 'MIGRATION_DEFAULT_HTTP_CLIENT_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_DEFAULT_HTTP_CLIENT_TS_INPUTS',
    },
    'default-http-client-additional': {
        'file': 'src/transaction/http/__tests/DefaultHttpClient.additional.test.ts',
        'java_class': 'com.metanet4j.bsv.transaction.http.DefaultHttpClientAdditionalTest',
        'test': 'DefaultHttpClientAdditionalTest',
        'probe': 'capture-default-http-client-additional-inputs.cjs',
        'ts_observations_env': 'MIGRATION_DEFAULT_HTTP_CLIENT_ADDITIONAL_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_DEFAULT_HTTP_CLIENT_ADDITIONAL_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记 http-chain 局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
