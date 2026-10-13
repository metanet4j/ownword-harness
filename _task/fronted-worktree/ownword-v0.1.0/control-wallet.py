#!/usr/bin/env python3
"""仅控制隔离 CWI 测试钱包；令牌留在服务侧运行配置。"""
import json
import sys
import urllib.request
from pathlib import Path

config = json.loads((Path(__file__).parent / '_runtime/services.json').read_text())
request = urllib.request.Request(
    config['OWNWORD_TEST_WALLET_URL'] + '/control',
    data=sys.argv[1].encode(),
    headers={'Content-Type': 'application/json',
             'Authorization': 'Bearer ' + config['OWNWORD_TEST_WALLET_TOKEN']},
    method='POST')
with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=10) as response:
    print(response.read().decode())
