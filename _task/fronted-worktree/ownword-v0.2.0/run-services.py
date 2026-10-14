#!/usr/bin/env python3
"""启动和管理本任务的真实本地服务，不输出运行配置中的凭据。"""
import argparse
import json
import os
import signal
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

task = Path(__file__).resolve().parent
runtime = task / '_runtime'
web = task / 'own-word-web'
jar_source = task.parents[1] / 'backend-worktree/ownword-v0.2.0/metanet4j-component/metanet4j-api-ownword/target/metanet4j-api-ownword-0.2.0.jar'
jar = runtime / 'metanet4j-api-ownword-0.2.0.jar'
java = Path('/home/haodev/.sdkman/candidates/java/25.0.4.1-tem/bin/java')
config = json.loads((runtime / 'services.json').read_text())
services = {
    'api': ([str(java), '-jar', str(jar), '--server.address=127.0.0.1', '--server.port=5073'], jar.name, task, 'http://127.0.0.1:5073/health'),
    'wallet': (['node', '--import', 'tsx', 'scripts/yours-wallet-server.ts'], 'scripts/yours-wallet-server.ts', web, config['OWNWORD_TEST_WALLET_URL'] + '/health'),
    'frontend': (['npm', 'start', '--', '--hostname', '127.0.0.1', '--port', '5071'], 'npm start', web, 'http://127.0.0.1:5071/'),
}

def process(name):
    path = runtime / (name + '.pid')
    if not path.exists():
        return None
    pid = int(path.read_text())
    proc = Path(f'/proc/{pid}')
    if not proc.exists():
        return None
    command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
    if not command:
        return None
    if services[name][1] not in command or name == 'api' and str(task.parents[2]) not in command:
        raise RuntimeError(f'{name} 的 PID 已被其他进程使用，未执行操作')
    return pid

def healthy(name):
    headers = {'Authorization': 'Bearer ' + config['OWNWORD_TEST_WALLET_TOKEN']} if name == 'wallet' else {}
    request = urllib.request.Request(services[name][3], headers=headers)
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=2) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False

def start(name):
    if process(name):
        print(name + ': 已运行')
        return
    command, _, cwd, _ = services[name]
    if name == 'api':
        shutil.copy2(jar_source, jar)
    with (runtime / (name + '.log')).open('a') as log:
        env = {**os.environ, **config}
        child = subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=log, start_new_session=True)
    (runtime / (name + '.pid')).write_text(str(child.pid))
    for _ in range(40):
        if child.poll() is not None:
            raise RuntimeError(name + ': 启动失败，查看本任务日志')
        if healthy(name):
            print(name + ': ready')
            return
        time.sleep(.25)
    raise RuntimeError(name + ': 未就绪，查看本任务日志')

def stop(name):
    pid = process(name)
    if not pid:
        return
    # npm 的子进程也属于本任务；逐个停止，避免误杀工具会话所在进程组。
    descendants = []
    def children(parent):
        for item in Path('/proc').iterdir():
            if not item.name.isdigit():
                continue
            try:
                status = (item / 'status').read_text()
                if f'PPid:\t{parent}\n' in status:
                    children(int(item.name))
                    if (item / 'cwd').resolve() != web and name == 'frontend':
                        raise RuntimeError('发现工作区外子进程，未停止')
                    descendants.append(int(item.name))
            except (FileNotFoundError, ProcessLookupError):
                pass
    children(pid)
    for target in [*descendants, pid]:
        try:
            os.kill(target, signal.SIGTERM)
        except ProcessLookupError:
            pass
    for _ in range(40):
        if not Path(f'/proc/{pid}').exists():
            break
        time.sleep(.1)
    print(name + ': 已停止')

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'])
parser.add_argument('service', nargs='?', default='all', choices=['all', *services])
args = parser.parse_args()
names = ['api', 'wallet', 'frontend'] if args.service == 'all' else [args.service]
for name in names:
    if args.action in ['stop', 'restart']:
        stop(name)
    if args.action in ['start', 'restart']:
        start(name)
    if args.action == 'status':
        print(name + ': ' + ('ready' if healthy(name) else 'unavailable'))
