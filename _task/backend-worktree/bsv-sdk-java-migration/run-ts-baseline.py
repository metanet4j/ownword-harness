#!/usr/bin/env python3
"""执行六模块真实 TS 基线；普通与 manual 分进程，逐项核对原始报告。"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

TASK = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(folder):
    manifest = read(folder / 'manifest.json')
    config = read(TASK / 'workspace.json')
    assert manifest['upstreamCommit'] == config['upstream']['commit'], '上游版本不同'
    assert manifest['catalogSha256'] == sha(TASK / 'module-tests.json'), '清单版本不同'
    subprocess.run([str(TASK / 'init.sh')], cwd=TASK, check=True)
    reports = []
    for group in ('standard', 'manual'):
        evidence = manifest['groups'][group]
        report = folder / f'{group}.jest.json'
        assert evidence['exitCode'] == 0, f'{group} 测试进程失败'
        assert evidence['command'], f'{group} 缺少执行命令'
        assert evidence['reportSha256'] == sha(report), f'{group} 报告已变'
        assert (folder / f'{group}.log').is_file(), f'{group} 缺少原始日志'
        assert (folder / f'{group}.resources.txt').is_file(), f'{group} 缺少资源记录'
        if evidence.get('networkPolicy') == 'audited-pure-computation':
            # 首次资源验收在 guard 建立前启动，仅执行已审查的原始 AES manual。
            assert group == 'manual' and manifest['manualFile'] == 'src/primitives/__tests/AESGCM.man.test.ts'
            sdk = TASK.parents[2] / config['upstream']['path'] / config['upstream']['packagePath']
            assert manifest['manualSha256'] == sha(sdk / manifest['manualFile']), 'manual 源码已变'
        else:
            assert evidence['guardSha256'] == sha(TASK / 'ts-offline-guard.cjs'), f'{group} 网络适配器版本不同'
            network_log = folder / f'{group}.network.jsonl'
            assert network_log.exists() and not network_log.read_text().strip(), f'{group} 存在真实网络请求或缺少记录'
        reports += ['--ts-report', str(report)]
    result = subprocess.run(['python3', str(TASK / 'audit-tests.py'), 'compare-ts', *reports], cwd=TASK, check=True, capture_output=True, text=True)
    summary = json.loads(result.stdout)
    summary['byModule'] = {}
    for group in ('standard', 'manual'):
        for suite in read(folder / f'{group}.jest.json')['testResults']:
            module = suite['name'].split('/src/')[1].split('/')[0]
            summary['byModule'][module] = summary['byModule'].get(module, 0) + len(suite['assertionResults'])
    manifest.update(status='passed', finishedAt=datetime.now(timezone.utc).isoformat(), summary=summary)
    (folder / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'evidence': str(folder), **summary}, ensure_ascii=False))


def run():
    config = read(TASK / 'workspace.json')
    catalog = read(TASK / 'module-tests.json')
    folder = Path(tempfile.mkdtemp(prefix='ts-baseline-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-', dir=TASK / '.cache/evidence'))
    sdk = TASK.parents[2] / config['upstream']['path'] / config['upstream']['packagePath']
    manifest = {'status': 'running', 'upstreamCommit': config['upstream']['commit'],
                'catalogSha256': sha(TASK / 'module-tests.json'), 'startedAt': datetime.now(timezone.utc).isoformat(),
                'nodeHeapMiB': 2048, 'groups': {}}
    subprocess.run([str(TASK / 'init.sh')], cwd=TASK, check=True)
    print('证据目录：' + str(folder), flush=True)
    for group, manual in [('standard', False), ('manual', True)]:
        tests = [f['path'] for f in catalog['files'] if ('.man.test.' in f['path']) == manual]
        assert tests, f'{group} 清单为空'
        command = [str(TASK / 'pnpm.sh'), '--dir', str(sdk), 'exec', 'jest', '--runInBand', '--watchman=false',
                   '--runTestsByPath', *tests, '--testPathIgnorePatterns', '/node_modules/',
                   '--setupFilesAfterEnv', str(TASK / 'ts-offline-guard.cjs'), '--json', '--outputFile=' + str(folder / f'{group}.jest.json')]
        network_log = folder / f'{group}.network.jsonl'
        network_log.touch()
        guard_sha = sha(TASK / 'ts-offline-guard.cjs')
        env = {**os.environ, 'NODE_OPTIONS': '--max-old-space-size=2048', 'MIGRATION_NETWORK_LOG': str(network_log)}
        with (folder / f'{group}.log').open('w') as log:
            result = subprocess.run(['/usr/bin/time', '-v', '-o', str(folder / f'{group}.resources.txt'),
                                     'timeout', '--kill-after=30s', '90m', *command], cwd=TASK, env=env, stdout=log, stderr=subprocess.STDOUT)
        report = folder / f'{group}.jest.json'
        manifest['groups'][group] = {'command': command, 'exitCode': result.returncode,
                                    'reportSha256': sha(report) if report.exists() else None,
                                    'guardSha256': guard_sha}
        (folder / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        print(f'{group} 进程退出 {result.returncode}，报告 {report}', flush=True)
    verify(folder)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', type=Path, help='复核已有完整运行目录，不重新执行测试')
    args = parser.parse_args()
    try:
        verify(args.verify.resolve()) if args.verify else run()
    except (AssertionError, KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f'TS 基线未通过：{error}')
