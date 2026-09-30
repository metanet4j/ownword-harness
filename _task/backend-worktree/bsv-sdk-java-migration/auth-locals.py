#!/usr/bin/env python3
"""auth 待采集原测试文件的登记表：原文件、Java 测试类、探针与环境变量。

`java_classes` 给出该原文件映射到的全部 Java 测试类（`peer` 的 Peer.test.ts 同时
映射到 PeerTest 与 PeerTransportErrorTest）；`test` 是 surefire `-Dtest=` 过滤式。
"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'peer': {
        'file': 'src/auth/__tests/Peer.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.PeerTest',
        'java_classes': ['com.metanet4j.bsv.auth.PeerTest',
                         'com.metanet4j.bsv.auth.PeerTransportErrorTest'],
        'test': 'PeerTest,PeerTransportErrorTest',
        'probe': 'capture-peer-inputs.cjs',
        'ts_observations_env': 'MIGRATION_AUTH_PEER_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_AUTH_PEER_TS_INPUTS',
    },
    'peer-certificate-policy': {
        'file': 'src/auth/__tests/Peer.certificatePolicy.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.PeerCertificatePolicyTest',
        'test': 'PeerCertificatePolicyTest',
        'probe': 'capture-peer-certificate-policy-inputs.cjs',
        'ts_observations_env': 'MIGRATION_AUTH_PEER_CERTIFICATE_POLICY_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_AUTH_PEER_CERTIFICATE_POLICY_TS_INPUTS',
    },
    'peer-boundary': {
        'file': 'src/auth/__tests/Peer.boundary.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.PeerBoundaryTest',
        'test': 'PeerBoundaryTest',
        'probe': 'capture-peer-boundary-inputs.cjs',
        'ts_observations_env': 'MIGRATION_AUTH_PEER_BOUNDARY_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_AUTH_PEER_BOUNDARY_TS_INPUTS',
    },
    'session-manager': {
        'file': 'src/auth/__tests/SessionManager.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.SessionManagerTest',
        'test': 'SessionManagerTest',
        'probe': 'capture-session-manager-inputs.cjs',
        'ts_observations_env': 'MIGRATION_AUTH_SESSION_MANAGER_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_AUTH_SESSION_MANAGER_TS_INPUTS',
    },
    'auth-build': {
        'file': 'src/auth/__tests/build.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.AuthBuildTest',
        'test': 'AuthBuildTest',
        'probe': 'capture-auth-build-inputs.cjs',
        'ts_observations_env': 'MIGRATION_AUTH_BUILD_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_AUTH_BUILD_TS_INPUTS',
    },
    'cryptononce': {
        'file': 'src/auth/utils/__tests/cryptononce.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.utils.CryptoNonceTest',
        'test': 'CryptoNonceTest',
        'probe': 'capture-cryptononce-inputs.cjs',
        'ts_observations_env': 'MIGRATION_AUTH_CRYPTONONCE_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_AUTH_CRYPTONONCE_TS_INPUTS',
    },
    'simplified-fetch-transport': {
        'file': 'src/auth/transports/__tests__/SimplifiedFetchTransport.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.transports.SimplifiedFetchTransportTest',
        'test': 'SimplifiedFetchTransportTest',
        'probe': 'capture-simplified-fetch-transport-inputs.cjs',
        'ts_observations_env': 'MIGRATION_AUTH_SIMPLIFIED_FETCH_TRANSPORT_TS_OBSERVATIONS',
        'inputs_env': 'MIGRATION_AUTH_SIMPLIFIED_FETCH_TRANSPORT_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记 auth 局部：' + name)
    entry = dict(LOCALS[name])
    entry.setdefault('java_classes', [entry['java_class']])
    entry['plan_path'] = TASK / f'{name}-input-plan.json'
    entry['probe_path'] = TASK / entry['probe']
    return entry
