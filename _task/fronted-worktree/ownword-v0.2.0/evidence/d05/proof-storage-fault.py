#!/usr/bin/env python3
"""隔离库中插入/清理一条损坏签名输入，验证服务重放失败后不会显示有效 Proof。"""
import json,sys,subprocess,urllib.parse
from pathlib import Path
task=Path(__file__).resolve().parents[2]
c=json.loads((task/'_runtime/services.json').read_text())
assert c['OWNWORD_DATABASE']=='ownword_v020'
f=json.loads((Path(__file__).parent/'proof-fixtures.json').read_text())['invalid']
p=urllib.parse.urlsplit(c['OWNWORD_MONGO_URI']);auth=p.netloc.rsplit('@',1)[0]+'@' if '@' in p.netloc else ''
uri=urllib.parse.urlunsplit(p._replace(netloc=auth+'127.0.0.1:27017'))
mode=sys.argv[1];assert mode in ['seed','clean']
js='const db=new Mongo('+json.dumps(uri)+').getDB("ownword_v020");const input='+json.dumps(f)+';'
if mode=='seed':js+='if(db.simulated_sync_receipts.countDocuments({txid:input.txid}))throw new Error("fixture exists");db.simulated_sync_receipts.insertOne(input);print("OWNWORD_FAULT=seeded");'
else:js+='const r=db.simulated_sync_receipts.deleteOne({txid:input.txid,qaFixture:"d05-invalid-signature"});print("OWNWORD_FAULT=cleaned:"+r.deletedCount);'
r=subprocess.run(['docker','exec','-i','infra-mongo','mongosh','--quiet','--nodb','--file','/dev/stdin'],input=js,text=True,capture_output=True)
if r.returncode:raise RuntimeError('隔离存储故障操作失败；连接信息不输出')
print(next(x for x in r.stdout.splitlines() if x.startswith('OWNWORD_FAULT=')))
