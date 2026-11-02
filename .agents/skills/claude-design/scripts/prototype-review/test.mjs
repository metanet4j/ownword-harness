// 验证真实静态预览、原生评论服务的持久化，以及文件和请求边界。
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,readFile,rm,mkdir,symlink} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {startReview} from './server.mjs';

test('静态原型评论：预览、持久化、隔离与请求边界',async t=>{
  const base=await mkdtemp(path.join(tmpdir(),'prototype-review-test-'));
  const root=path.join(base,'first'), second=path.join(base,'second');
  const original='<!doctype html><html><body><button id="fixture">原型操作</button><script src="app.js"></script></body></html>';
  for(const dir of [root,second]){await mkdir(dir);await writeFile(path.join(dir,'index.html'),original);}
  const bytes=Buffer.from([0,1,2,240,255]);await writeFile(path.join(root,'asset.png'),bytes);
  await writeFile(path.join(root,'app.js'),'window.fixtureLoaded=true;');
  await writeFile(path.join(base,'outside.txt'),'private');
  await symlink(path.join(base,'outside.txt'),path.join(root,'outside.txt'));
  let app,other;
  t.after(async()=>{if(other)await other.close();if(app)await app.close();await rm(base,{recursive:true,force:true});});
  app=await startReview(root,{port:0});
  const endpoint=()=>app.url+'__prototype-review/comments';
  const call=(url,method,data,origin)=>fetch(url,{method,headers:{'Content-Type':'application/json',...(origin?{Origin:origin}:{})},...(data!==undefined?{body:JSON.stringify(data)}:{})});
  const a={prototype:1,url:'/#/content',selector:'#fixture',rect:{x:.5,y:.5,w:0,h:0},area:false,viewport:{width:1440,height:1000}};
  let id;
  await t.test('保留原型和资源字节，只在 HTTP 响应添加工具入口',async()=>{
    const response=await fetch(app.url),html=await response.text();
    assert.equal(response.status,200);assert.equal(response.headers.get('cache-control'),'no-store');
    assert.ok(html.includes('id="fixture"'));assert.ok(html.includes('/__prototype-review/client.js'));
    assert.equal(await readFile(path.join(root,'index.html'),'utf8'),original);
    assert.deepEqual(Buffer.from(await(await fetch(app.url+'asset.png')).arrayBuffer()),bytes);
    assert.equal((await fetch(app.url+'__prototype-review/client.js')).status,200);
  });
  await t.test('拒绝跨站写入、隐藏目录和目录外链接',async()=>{
    assert.equal((await fetch(app.url+'.prototype-review/comments.json')).status,403);
    assert.equal((await fetch(app.url+'outside.txt')).status,403);
    assert.equal((await call(endpoint(),'POST',{anchor:JSON.stringify(a),label:'按钮',text:'意见'},'https://elsewhere.example')).status,403);
    assert.equal((await call(endpoint(),'POST',{anchor:JSON.stringify(a),label:'按钮',text:'   '})).status,400);
    assert.equal((await(await fetch(endpoint())).json()).threads.length,0);
  });
  await t.test('调用原生评论保存、回复、解决和重新打开',async()=>{
    const response=await call(endpoint(),'POST',{anchor:JSON.stringify(a),label:'内容列表 · 按钮',text:'请检查对齐'});
    assert.equal(response.status,201);const thread=(await response.json()).thread;id=thread.id;
    assert.equal(JSON.parse(thread.anchor).url,'/#/content');
    assert.equal((await call(endpoint()+'/'+id+'/messages','POST',{text:'已记录'})).status,200);
    assert.equal((await call(endpoint()+'/'+id,'PATCH',{status:'resolved'})).status,200);
    assert.equal((await(await fetch(endpoint())).json()).threads[0].status,'resolved');
    assert.equal((await call(endpoint()+'/'+id,'PATCH',{status:'open'})).status,200);
    const saved=JSON.parse(await readFile(path.join(app.store,'comments.json'),'utf8'));
    assert.equal(saved.version,1);assert.equal(saved.threads[0].messages.length,2);
  });
  await t.test('重启恢复评论，另一原型使用独立的评论数据',async()=>{
    await app.close();app=null;app=await startReview(root,{port:0});
    assert.equal((await(await fetch(endpoint())).json()).threads[0].id,id);
    other=await startReview(second,{port:0});
    assert.equal((await(await fetch(other.url+'__prototype-review/comments')).json()).threads.length,0);
    assert.equal((await call(endpoint()+'/'+id,'DELETE')).status,200);
    assert.equal((await(await fetch(endpoint())).json()).threads.length,0);
  });
});
