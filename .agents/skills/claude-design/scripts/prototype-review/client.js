// 预览工具的样式与交互独立于业务框架；用户文字只作为 textContent 渲染。
(() => {
  if (document.getElementById('prototype-review-tools')) return;
  const api='/__prototype-review', host=document.createElement('div');
  host.id='prototype-review-tools'; document.body.append(host);
  const ui=host.attachShadow({mode:'open'});
  ui.innerHTML=`<style>
:host{all:initial;position:fixed;inset:0;z-index:2147483646;pointer-events:none;font:14px/1.5 system-ui,sans-serif;color:#242424;--bg:#fff;--fg:#242424;--muted:#626262;--border:#ccc;--accent:#2856dd;--on-accent:#fff;--soft:#f4f5f7;color-scheme:light}
:host([data-theme=dark]){--bg:#242424;--fg:#f5f5f5;--muted:#bbb;--border:#666;--accent:#a7bfff;--on-accent:#172143;--soft:#333;color:#f5f5f5;color-scheme:dark}
*{box-sizing:border-box} [hidden]{display:none!important}button,input,textarea{font:inherit}button{cursor:pointer;border:1px solid var(--border);border-radius:7px;background:var(--bg);color:var(--fg);min-height:44px;padding:8px 12px}button:hover{background:var(--soft)}button:focus-visible,input:focus-visible,textarea:focus-visible{outline:3px solid var(--accent);outline-offset:2px}button:disabled{opacity:.55;cursor:default}.primary,[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}.primary:hover,[aria-pressed=true]:hover{filter:brightness(.95);background:var(--accent)}
.dock{position:fixed;right:16px;bottom:72px;display:flex;gap:6px;pointer-events:auto;padding:6px;background:var(--bg);border:1px solid var(--border);border-radius:11px;box-shadow:0 3px 14px #0002}.hint{position:fixed;right:16px;bottom:140px;max-width:calc(100vw - 32px);padding:8px 12px;background:var(--accent);color:var(--on-accent);border-radius:7px}.panel{pointer-events:auto;position:fixed;right:16px;bottom:140px;width:350px;max-width:calc(100vw - 32px);max-height:calc(100dvh - 170px);overflow:auto;background:var(--bg);color:var(--fg);border:1px solid var(--border);border-radius:12px;box-shadow:0 6px 28px #0003;padding:16px}.head,.actions{display:flex;align-items:center;gap:8px;justify-content:space-between}.head h2{font-size:17px;line-height:1.4;margin:0}.head button{padding:4px 10px}.muted{color:var(--muted);font-size:12px;overflow-wrap:anywhere}.context{margin:8px 0 12px}.actions{justify-content:flex-end;margin-top:10px}.actions.wrap{flex-wrap:wrap;justify-content:flex-start}.field{display:block;margin:12px 0 5px}textarea{width:100%;min-height:100px;resize:vertical;padding:9px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--fg)}.error{color:#b42318;white-space:pre-wrap;margin:8px 0}:host([data-theme=dark]) .error{color:#ffb4ab}.status{color:var(--muted);font-size:12px;margin:8px 0}.threads{margin-top:12px}.thread{display:block;text-align:left;width:100%;margin:7px 0;padding:10px;overflow-wrap:anywhere}.thread span{display:block}.messages article{padding:10px 0;border-bottom:1px solid var(--border)}.messages p{white-space:pre-wrap;overflow-wrap:anywhere;margin:5px 0}.messages strong{font-size:12px}.filter{display:flex;align-items:center;gap:8px;min-height:40px;margin-top:8px}.filter input{width:18px;height:18px}.outline{position:fixed;border:2px solid var(--accent);background:#2856dd12;pointer-events:none}.pin{pointer-events:auto;position:fixed;transform:translate(-50%,-50%);width:44px;height:44px;min-height:44px;padding:0;border:0;background:transparent;display:grid;place-items:center}.pin span{display:grid;place-items:center;background:var(--accent);color:var(--on-accent);border:2px solid var(--bg);border-radius:50%;width:28px;height:28px;box-shadow:0 1px 5px #0005}.pin:hover{background:transparent}.pin.resolved span{background:var(--muted);color:var(--bg)}
@media(max-width:480px){.panel{bottom:140px;max-height:60dvh}.dock{right:12px}.hint{right:12px}}
</style>
<div class="outline" id="outline" hidden></div><div id="pins"></div>
<div class="hint" id="hint" role="status" hidden>点击元素或拖动框选；按 Esc 退出标注</div>
<aside class="panel" id="panel" role="dialog" aria-modal="false" aria-labelledby="title" hidden>
<div class="head"><h2 id="title">页面评论</h2><button id="close" type="button" aria-label="关闭评论面板">关闭</button></div>
<p class="muted context" id="context"></p><div id="form-error" class="error" role="alert"></div>
<form id="compose" hidden><label class="field" for="comment">评论内容</label><textarea id="comment" maxlength="10000" placeholder="说明这里需要怎样调整" required></textarea><div class="actions"><button id="cancel" type="button">取消</button><button id="save" class="primary" type="submit">保存评论</button></div></form>
<section id="detail" hidden><div class="messages" id="messages"></div><div class="actions wrap"><button id="resolve" type="button">标记已解决</button><button id="remove" type="button">删除评论</button></div><form id="reply-form"><label class="field" for="reply">回复内容</label><textarea id="reply" maxlength="10000" required></textarea><div class="actions"><button class="primary" id="reply-save" type="submit">保存回复</button></div></form></section>
<section id="list-view"><button id="add" class="primary" type="button">添加评论</button><label class="filter"><input id="resolved" type="checkbox">显示已解决</label><div class="threads" id="threads"></div></section><p class="status" id="status" role="status"></p>
</aside>
<div class="dock" aria-label="原型评审工具"><button id="pick" type="button" aria-pressed="false" title="Alt+Shift+C 进入或退出标注">评论</button><button id="list" type="button" aria-expanded="false">评论列表 <span id="count">0</span></button></div>`;
  const $=id=>ui.getElementById(id), state={threads:[],meta:{},selecting:false,drag:null,pending:null,selected:null,busy:false,blockClickUntil:0};
  const pins=new Map(), route=()=>location.pathname+location.search+location.hash;
  const ours=e=>e.composedPath().includes(host);
  const text=(tag,value,className)=>{const e=document.createElement(tag);e.textContent=value;if(className)e.className=className;return e;};
  function anchor(thread){try{const a=JSON.parse(thread.anchor);return a?.prototype===1&&typeof a.url==='string'&&typeof a.selector==='string'&&['x','y','w','h'].every(k=>Number.isFinite(a.rect?.[k]))?a:null;}catch{return null;}}
  const pageTitle=()=>document.querySelector('main h1, #main h1, h1')?.textContent.trim()??document.title;
  const current=()=>state.threads.filter(t=>anchor(t)?.url===route());
  const wanted=()=>current().filter(t=>t.status==='open'||$('resolved').checked);
  function label(el){return (el.getAttribute('aria-label')||el.labels?.[0]?.textContent||el.getAttribute('placeholder')||el.innerText||el.textContent||el.localName).replace(/\s+/g,' ').trim().slice(0,140);}
  function selector(el){
    const parts=[];
    for(let p=el;p&&p!==document.documentElement;p=p.parentElement){
      if(p.id&&!/^(react-aria|:r)/.test(p.id)&&document.querySelectorAll('#'+CSS.escape(p.id)).length===1){parts.unshift('#'+CSS.escape(p.id));break;}
      const tag=p.localName,siblings=p.parentElement?Array.from(p.parentElement.children).filter(s=>s.localName===tag):[p];
      parts.unshift(tag+(siblings.length>1?`:nth-of-type(${siblings.indexOf(p)+1})`:''));
    }
    return parts.join(' > ');
  }
  const hit=(x,y)=>{const e=document.elementFromPoint(x,y);return !e||e===host?null:e.closest('button,a,input,textarea,select,[contenteditable="true"]')||e;};
  function makeAnchor(start,end){
    const area=Math.hypot(end.x-start.x,end.y-start.y)>8;
    let el=start.el;
    if(area){const last=hit(end.x,end.y);while(el.parentElement&&last&&!el.contains(last))el=el.parentElement;}
    let sel=selector(el);if(sel.length>1000){el=document.body;sel='body';}
    const b=el.getBoundingClientRect();
    const left=area?Math.min(start.x,end.x):start.x,top=area?Math.min(start.y,end.y):start.y;
    const title=pageTitle();
    return {prototype:1,url:route(),pageTitle:title,selector:sel,rect:{x:(left-b.left)/Math.max(b.width,1),y:(top-b.top)/Math.max(b.height,1),w:area?Math.abs(end.x-start.x)/Math.max(b.width,1):0,h:area?Math.abs(end.y-start.y)/Math.max(b.height,1):0},area,label:area?'区域 · '+title.slice(0,80):label(el),viewport:{width:innerWidth,height:innerHeight},language:document.documentElement.lang,theme:document.documentElement.dataset.colorScheme??getComputedStyle(document.body).colorScheme,version:state.meta.version??null};
  }
  function rect(a){
    if(a.url!==route()||(a.pageTitle&&a.pageTitle!==pageTitle()))return null;
    let el;try{el=document.querySelector(a.selector);}catch{return null;}
    if(!el||el===host)return null;
    if(!a.area&&a.label&&a.label!==label(el))return null;
    const b=el.getBoundingClientRect();if(!b.width||!b.height)return null;
    return {left:b.left+b.width*a.rect.x,top:b.top+b.height*a.rect.y,width:b.width*a.rect.w,height:b.height*a.rect.h};
  }
  function outline(box){$('outline').hidden=!box;if(box)Object.assign($('outline').style,{left:box.left+'px',top:box.top+'px',width:Math.max(box.width,3)+'px',height:Math.max(box.height,3)+'px'});}
  function measure(){
    const dark=document.documentElement.dataset.colorScheme==='dark';host.dataset.theme=dark?'dark':'light';
    const visible=new Set(), show=!$('panel').hidden||state.selecting;
    wanted().forEach((t,i)=>{
      const a=anchor(t),r=a&&rect(a);if(!show||!r||r.top<-44||r.top>innerHeight||r.left<-44||r.left>innerWidth)return;
      visible.add(t.id);let pin=pins.get(t.id);
      if(!pin){pin=document.createElement('button');pin.type='button';pin.append(text('span',''));pin.onclick=()=>openThread(t.id);$('pins').append(pin);pins.set(t.id,pin);}
      pin.firstChild.textContent=String(i+1);pin.className='pin'+(t.status==='resolved'?' resolved':'');
      pin.setAttribute('aria-label',`评论 ${i+1}：${t.messages[0]?.text.slice(0,80)??''}`);pin.style.left=r.left+'px';pin.style.top=r.top+'px';
    });
    for(const [id,pin] of pins)if(!visible.has(id)){pin.remove();pins.delete(id);}
    if(state.pending)outline(rect(state.pending));
    else if(!state.selecting){const selected=anchor(state.threads.find(t=>t.id===state.selected)??{});outline(selected?.area?rect(selected):null);}
  }
  let queued=false;
  function schedule(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;measure();});}
  function formState(){
    $('save').disabled=state.busy||!$('comment').value.trim();$('reply-save').disabled=state.busy||!$('reply').value.trim();
    $('resolve').disabled=state.busy;$('remove').disabled=state.busy;
  }
  function render(){
    $('count').textContent=String(current().filter(t=>t.status==='open').length);
    $('threads').replaceChildren();
    for(const t of wanted()){
      const b=document.createElement('button');b.type='button';b.className='thread';
      b.append(text('span',t.messages[0]?.text??''),text('span',(t.status==='resolved'?'已解决 · ':'')+(anchor(t)?.label??''),'muted'));
      b.onclick=()=>openThread(t.id);$('threads').append(b);
    }
    if(!wanted().length)$('threads').append(text('p','本页还没有评论。','muted'));
    if(state.selected){
      const t=state.threads.find(t=>t.id===state.selected);
      if(!t){state.selected=null;showList();}else{
        $('messages').replaceChildren();
        for(const m of t.messages){const item=document.createElement('article');item.append(text('strong',m.author.name+(m.author.kind==='agent'?' · 代理':'')),text('p',m.text));$('messages').append(item);}
        $('resolve').textContent=t.status==='resolved'?'重新打开':'标记已解决';
      }
    }
    formState();schedule();
  }
  function setSelecting(value){state.selecting=value;state.drag=null;$('pick').setAttribute('aria-pressed',String(value));$('pick').textContent=value?'退出标注':'评论';$('hint').hidden=!value;if(!value&&!state.pending)outline(null);schedule();}
  function showList(){state.pending=null;state.selected=null;$('panel').hidden=false;$('compose').hidden=true;$('detail').hidden=true;$('list-view').hidden=false;$('title').textContent='页面评论';$('context').textContent=route();$('list').setAttribute('aria-expanded','true');$('form-error').textContent='';outline(null);render();}
  function openThread(id){setSelecting(false);state.pending=null;state.selected=id;$('panel').hidden=false;$('compose').hidden=true;$('detail').hidden=false;$('list-view').hidden=true;$('title').textContent='评论详情';$('context').textContent=state.threads.find(t=>t.id===id)?.label??'';$('reply').value='';$('form-error').textContent='';$('list').setAttribute('aria-expanded','true');outline(null);render();$('reply').focus({preventScroll:true});}
  function close(){setSelecting(false);state.pending=null;state.selected=null;$('panel').hidden=true;$('list').setAttribute('aria-expanded','false');outline(null);schedule();$('pick').focus({preventScroll:true});}
  function select(){
    if(state.selecting)return close();
    if(state.pending&&$('comment').value.trim()&&!confirm('放弃尚未保存的评论，重新选择位置？'))return;
    state.pending=null;state.selected=null;$('panel').hidden=true;$('list').setAttribute('aria-expanded','false');$('form-error').textContent='';setSelecting(true);
  }
  async function request(suffix='',options={}){
    let r;try{r=await fetch(api+'/comments'+suffix,{...options,headers:{'Content-Type':'application/json'}});}
    catch{throw new Error('无法连接评论服务。文字已保留，请重试。');}
    let data;try{data=await r.json();}catch{throw new Error('评论服务返回异常，请保留文字并重试。');}
    if(!r.ok)throw new Error(data.message??'评论操作失败，请重试。');return data;
  }
  async function action(fn){if(state.busy)return;state.busy=true;$('form-error').textContent='';formState();try{await fn();}catch(e){$('form-error').textContent=e.message;}finally{state.busy=false;formState();}}
  function upsert(t){state.threads=state.threads.filter(x=>x.id!==t.id).concat(t);render();}
  $('pick').onclick=select;$('add').onclick=select;$('close').onclick=close;$('cancel').onclick=close;
  $('list').onclick=()=>{$('panel').hidden?(setSelecting(false),showList()):close();};
  $('resolved').onchange=render;$('comment').oninput=formState;$('reply').oninput=formState;
  $('compose').onsubmit=e=>{e.preventDefault();void action(async()=>{
    const a=state.pending;if(!a)return;
    const data=await request('',{method:'POST',body:JSON.stringify({anchor:JSON.stringify(a),label:route()+' · '+a.label,detail:`真实原型页面 ${route()}；元素 ${a.selector}；版本 ${a.version??'未登记'}；${a.viewport.width}×${a.viewport.height}；${a.language}／${a.theme}`,area:a.area,text:$('comment').value})});
    $('comment').value='';state.pending=null;upsert(data.thread);openThread(data.thread.id);
  });};
  $('reply-form').onsubmit=e=>{e.preventDefault();void action(async()=>{const data=await request('/'+state.selected+'/messages',{method:'POST',body:JSON.stringify({text:$('reply').value})});$('reply').value='';upsert(data.thread);});};
  $('resolve').onclick=()=>void action(async()=>{const t=state.threads.find(t=>t.id===state.selected);if(!t)return;upsert((await request('/'+t.id,{method:'PATCH',body:JSON.stringify({status:t.status==='resolved'?'open':'resolved'})})).thread);});
  $('remove').onclick=()=>{if(!confirm('删除这条评论及全部回复？'))return;void action(async()=>{await request('/'+state.selected,{method:'DELETE'});state.threads=state.threads.filter(t=>t.id!==state.selected);state.selected=null;showList();});};
  document.addEventListener('pointerdown',e=>{
    if(!state.selecting){state.blockClickUntil=0;return;}
    if(ours(e)||e.button!==0)return;
    const el=hit(e.clientX,e.clientY);if(!el)return;
    e.preventDefault();e.stopImmediatePropagation();state.drag={x:e.clientX,y:e.clientY,el,id:e.pointerId};
  },true);
  document.addEventListener('pointermove',e=>{
    if(!state.selecting||ours(e))return;
    if(state.drag){const d=state.drag;outline({left:Math.min(d.x,e.clientX),top:Math.min(d.y,e.clientY),width:Math.abs(d.x-e.clientX),height:Math.abs(d.y-e.clientY)});}
    else{const el=hit(e.clientX,e.clientY);if(el)outline(el.getBoundingClientRect());}
  },true);
  document.addEventListener('pointerup',e=>{
    const start=state.drag;if(!state.selecting||!start||start.id!==e.pointerId)return;
    e.preventDefault();e.stopImmediatePropagation();state.blockClickUntil=performance.now()+300;state.pending=makeAnchor(start,{x:e.clientX,y:e.clientY});setSelecting(false);
    $('title').textContent='添加评论';$('context').textContent=state.pending.label;$('panel').hidden=false;$('compose').hidden=false;$('detail').hidden=true;$('list-view').hidden=true;$('list').setAttribute('aria-expanded','true');$('comment').value='';formState();schedule();$('comment').focus({preventScroll:true});
  },true);
  document.addEventListener('pointercancel',()=>{state.drag=null;outline(null);},true);
  document.addEventListener('click',e=>{if(!ours(e)&&(state.selecting||performance.now()<state.blockClickUntil)){state.blockClickUntil=0;e.preventDefault();e.stopImmediatePropagation();}},true);
  document.addEventListener('keydown',e=>{
    if(e.isComposing)return;
    if(e.altKey&&e.shiftKey&&e.code==='KeyC'){e.preventDefault();select();}
    else if(e.key==='Escape'&&(state.selecting||(!$('panel').hidden&&ui.activeElement))){e.preventDefault();e.stopImmediatePropagation();close();}
  },true);
  const moved=()=>{if(state.selecting)setSelecting(false);if(state.pending&&state.pending.url!==route())close();if(!$('panel').hidden&&!state.pending)showList();render();};
  addEventListener('hashchange',moved);addEventListener('popstate',moved);addEventListener('resize',schedule);document.addEventListener('scroll',schedule,true);
  new MutationObserver(schedule).observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['class','style','data-color-scheme']});
  fetch(api+'/meta').then(r=>r.json()).then(meta=>{state.meta=meta;}).catch(()=>{});
  request().then(data=>{state.threads=data.threads;render();}).catch(e=>{$('status').textContent=e.message;});
  const live=new EventSource(api+'/comments/events');
  live.addEventListener('comments',e=>{try{const data=JSON.parse(e.data);state.threads=data.threads;$('status').textContent='评论已同步；写好后可在对话中通知代理读取。';render();}catch{$('status').textContent='评论同步异常，可稍后重试。';}});
  live.onerror=()=>{$('status').textContent='评论连接暂时中断，未保存的文字会保留。';};
  formState();schedule();
})();
