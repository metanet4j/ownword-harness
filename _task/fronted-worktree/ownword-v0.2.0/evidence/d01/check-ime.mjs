import {execFileSync} from 'node:child_process';
const cdp=JSON.parse(execFileSync('agent-browser',['--session','v020-implementation','get','cdp-url','--json'],{encoding:'utf8'})).data.cdpUrl;
const ws=new WebSocket(cdp),pending=new Map();let id=0;
await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
ws.addEventListener('message',event=>{const result=JSON.parse(event.data);if(result.id){const task=pending.get(result.id);pending.delete(result.id);clearTimeout(task.timer);result.error?task.reject(new Error(JSON.stringify(result.error))):task.resolve(result.result);}});
function call(method,params={},sessionId){return new Promise((resolve,reject)=>{const next=++id;const timer=setTimeout(()=>reject(new Error('CDP_TIMEOUT')),10000);pending.set(next,{resolve,reject,timer});ws.send(JSON.stringify({id:next,method,params,sessionId}));});}
try{
 const {targetInfos}=await call('Target.getTargets');const pages=targetInfos.filter(t=>t.type==='page'&&t.url.startsWith('http://127.0.0.1:5071/content/drafts/'));if(pages.length!==1)throw new Error('AMBIGUOUS_OWNWORD_TEST_PAGE');
 const {sessionId}=await call('Target.attachToTarget',{targetId:pages[0].targetId,flatten:true});
 for(const text of ['zhong','中文','中文组合输入'])await call('Input.imeSetComposition',{text,selectionStart:text.length,selectionEnd:text.length},sessionId);
 await call('Input.insertText',{text:'中文组合输入'},sessionId);
 console.log('已在 agent-browser 管理的当前页面执行原生 IME 候选更新及提交。');
} finally {ws.close();}
