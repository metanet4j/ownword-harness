#!/usr/bin/env python3
"""auth-certificates 六个局部的登记表：文件、Java 测试、TS 探针与版本化计划。"""
from pathlib import Path

TASK = Path(__file__).resolve().parent

LOCALS = {
    'auth-master-certificate-constructors': {
        'file': 'src/auth/certificates/__tests/MasterCertificate.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.certificates.MasterCertificateTest',
        'test': 'MasterCertificateTest',
        'probe': 'capture-auth-certificate-master-constructor.cjs',
        'plan': 'auth-certificate-master-constructor-plan.json',
        'inputs_env': 'MIGRATION_AUTH_CERTIFICATE_TS_INPUTS',
    },
    'auth-master-certificate-remaining': {
        'file': 'src/auth/certificates/__tests/MasterCertificate.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.certificates.MasterCertificateTest',
        'test': 'MasterCertificateTest',
        'probe': 'capture-auth-certificate-master-remaining.cjs',
        'plan': 'auth-certificate-master-remaining-plan.json',
        'inputs_env': 'MIGRATION_AUTH_CERTIFICATE_MASTER_REMAINING_TS_INPUTS',
    },
    'auth-get-verifiable-certificates': {
        'file': 'src/auth/utils/__tests/getVerifiableCertificates.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.utils.GetVerifiableCertificatesTest',
        'test': 'GetVerifiableCertificatesTest',
        'probe': 'capture-auth-certificate-get-verifiable.cjs',
        'plan': 'auth-certificate-get-verifiable-plan.json',
        'inputs_env': 'MIGRATION_AUTH_CERTIFICATE_GET_VERIFIABLE_TS_INPUTS',
    },
    'auth-validate-certificates': {
        'file': 'src/auth/utils/__tests/validateCertificates.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.utils.ValidateCertificatesTest',
        'test': 'ValidateCertificatesTest',
        'probe': 'capture-auth-certificate-validate.cjs',
        'plan': 'auth-certificate-validate-plan.json',
        'inputs_env': 'MIGRATION_AUTH_CERTIFICATE_VALIDATE_TS_INPUTS',
    },
    'auth-certificate-class': {
        'file': 'src/auth/certificates/__tests/Certificate.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.certificates.CertificateTest',
        'test': 'CertificateTest',
        'probe': 'capture-auth-certificate-class.cjs',
        'plan': 'auth-certificate-class-plan.json',
        'inputs_env': 'MIGRATION_AUTH_CERTIFICATE_CLASS_TS_INPUTS',
    },
    'auth-verifiable-certificate': {
        'file': 'src/auth/certificates/__tests/VerifiableCertificate.test.ts',
        'java_class': 'com.metanet4j.bsv.auth.certificates.VerifiableCertificateTest',
        'test': 'VerifiableCertificateTest',
        'probe': 'capture-auth-certificate-verifiable.cjs',
        'plan': 'auth-certificate-verifiable-plan.json',
        'inputs_env': 'MIGRATION_AUTH_CERTIFICATE_VERIFIABLE_TS_INPUTS',
    },
}


def local(name):
    if name not in LOCALS:
        raise ValueError('未登记证书局部：' + name)
    entry = dict(LOCALS[name])
    entry['plan_path'] = TASK / entry['plan']
    entry['probe_path'] = TASK / entry['probe']
    return entry


def fragment(name):
    """按局部用例集合裁剪固定清单与映射，供标准采集与门禁使用。"""
    import importlib.util
    import json

    spec = importlib.util.spec_from_file_location('audit_tests', TASK / 'audit-tests.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    entry = local(name)
    plan = json.loads(entry['plan_path'].read_text())
    catalog = json.loads((TASK / 'module-tests.json').read_text())
    mapping = json.loads((TASK / 'test-map.json').read_text())
    file = next(item for item in catalog['files'] if item['path'] == entry['file'])
    ids = set(plan)
    cases = [case for case in file['cases'] if case['id'] in ids]
    if {case['id'] for case in cases} != ids:
        raise ValueError('计划用例不在固定文件中：' + name)
    mapped = [case for case in mapping['cases'] if case['id'] in ids]
    sites = {site for case in mapped for site in case['assertionIds']}
    review = {item['id'] for item in mapping['siteReviews'] if set(item['caseIds']) <= ids}
    sites |= review
    fragment_catalog = {**catalog, 'files': [{**file, 'cases': cases,
                                              'sites': [site for site in file['sites'] if site['id'] in sites]}],
                        'partialImplementationOnly': True}
    fragment_mapping = {**mapping, 'cases': mapped,
                        'siteReviews': [item for item in mapping['siteReviews'] if item['id'] in sites]}
    audit.validate_plan(fragment_catalog, fragment_mapping, plan)
    return entry, fragment_catalog, fragment_mapping, plan
