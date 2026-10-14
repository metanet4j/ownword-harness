// 真实签名交易经隔离 API 入库；故意不提交前版，检查历史缺失界面。
import { post, authorBapId } from '../../own-word-web/tests/post-helpers.mts';
import { writeFile } from 'node:fs/promises';
const base = 'http://127.0.0.1:5073/api/v1';
async function send(tx) {
  const txid = tx.id('hex');
  const response = await fetch(`${base}/transactions/sync`, {method:'POST', headers:{'Content-Type':'application/json','Idempotency-Key':txid},body:JSON.stringify({operationId:crypto.randomUUID(),bapId:authorBapId,txid,rawTx:tx.toHex()})});
  if (!response.ok) throw new Error(`sync ${response.status}`);
  return txid;
}
const root = await post(`# 历史缺失验收 ${crypto.randomUUID()}`), rootTxid = await send(root);
const parent = await post('尚未取得的前版',{rootTxid,previousTxid:rootTxid});
const child = await post('# 已取得第三版\n\n前版缺失时不能冒充最新。',{rootTxid,previousTxid:parent.id('hex')});
const txid = await send(child);
const response = await fetch(`${base}/contents/${txid}`), body = await response.json();
if (response.status !== 202 || body.data.revision.status !== 'incomplete' || body.data.revision.revisionNo !== null) throw new Error('incomplete relation expected');
await writeFile(new URL('./incomplete-fixture.json',import.meta.url),JSON.stringify({txid,rootTxid,missingPreviousTxid:parent.id('hex'),response:body},null,2)+'\n');
console.log(JSON.stringify({txid,rootTxid,status:response.status,relation:body.data.revision.status}));
