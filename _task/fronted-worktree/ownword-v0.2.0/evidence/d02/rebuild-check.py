#!/usr/bin/env python3
"""只清除本任务指定测试作者的可重建投影；保留所有同步原交易。"""
import json
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

task = Path(__file__).resolve().parents[2]
config = json.loads((task / '_runtime/services.json').read_text())
assert config['OWNWORD_DATABASE'] == 'ownword_v020'
parts = urllib.parse.urlsplit(config['OWNWORD_MONGO_URI'])
auth = parts.netloc.rsplit('@', 1)[0] + '@' if '@' in parts.netloc else ''
uri = urllib.parse.urlunsplit(parts._replace(netloc=auth + '127.0.0.1:27017'))
vectors = json.loads((task.parents[1] / 'backend-worktree/ownword-v0.2.0/metanet4j-component/metanet4j-api-ownword/src/test/resources/post-vectors.json').read_text())
author = vectors['authorBapId']
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def read(path):
    with opener.open('http://127.0.0.1:5073/api/v1/' + path, timeout=40) as response:
        return json.load(response)['data']

def mongo(source):
    program = 'const conn = new Mongo(' + json.dumps(uri) + '); const store = conn.getDB("ownword_v020");\n' + source
    result = subprocess.run(['docker', 'exec', '-i', 'infra-mongo', 'mongosh', '--quiet', '--nodb', '--file', '/dev/stdin'],
                            input=program, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError('本任务 Mongo 检查失败，未输出连接凭据')
    lines = [line for line in result.stdout.splitlines() if line.startswith('OWNWORD_CHECK=')]
    if len(lines) != 1:
        raise RuntimeError('Mongo 检查输出无效')
    return json.loads(lines[0].removeprefix('OWNWORD_CHECK='))

items = read('contents?authorBapId=' + author)['items']
ids = [item['txid'] for item in items[:3]]
assert len(ids) == 3
before = {txid: read('contents/' + txid) for txid in ids}
assert all(value['authorBapId'] == author for value in before.values())
deleted = mongo('const ids = ' + json.dumps(ids) + ''';
const receipts = store.simulated_sync_receipts.countDocuments({txid: {$in: ids}});
if (receipts !== ids.length) throw new Error("Missing raw sources");
const contents = store.simulated_contents.deleteMany({txid: {$in: ids}}).deletedCount;
const relations = store.simulated_content_relations.deleteMany({txid: {$in: ids}}).deletedCount;
print("OWNWORD_CHECK=" + JSON.stringify({receipts, contents, relations}));
''')
assert deleted == {'receipts': 3, 'contents': 3, 'relations': 3}, deleted
subprocess.run(['python3', str(task / 'run-services.py'), 'restart', 'api'], check=True)
after = {txid: read('contents/' + txid) for txid in ids}
fields = ['txid', 'authorBapId', 'markdown', 'contentDigest', 'firstObservedAt', 'revision', 'proof']
assert all({field: before[id][field] for field in fields} == {field: after[id][field] for field in fields} for id in ids)
rebuilt = mongo('const ids = ' + json.dumps(ids) + ''';
print("OWNWORD_CHECK=" + JSON.stringify({contents: store.simulated_contents.countDocuments({txid: {$in: ids}}),
relations: store.simulated_content_relations.countDocuments({txid: {$in: ids}}),
receipts: store.simulated_sync_receipts.countDocuments({txid: {$in: ids}})}));
''')
assert rebuilt == {'contents': 3, 'relations': 3, 'receipts': 3}, rebuilt
result = {'passed': True, 'database': 'ownword_v020', 'authorBapId': author, 'txids': ids,
          'deleted': deleted, 'rebuilt': rebuilt, 'comparedFields': fields, 'coldProcess': True}
(Path(__file__).parent / 'rebuild-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
