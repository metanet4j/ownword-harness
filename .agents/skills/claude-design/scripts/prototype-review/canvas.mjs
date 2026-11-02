// 将结构化 DOM 副本交给原生画布；沿用原生冲突检测、历史和资源上传。
import {readFile,realpath,mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {createHash,randomUUID} from 'node:crypto';
import path from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const exec=promisify(execFile);
const tags=new Set('div span main header footer nav section article aside h1 h2 h3 h4 h5 h6 p a button img label ul ol li dl dt dd strong em b i small code pre blockquote hr br table thead tbody tfoot tr th td figure figcaption form fieldset legend details summary time address q s del ins sub sup kbd samp mark svg g path rect circle ellipse line polyline polygon defs linearGradient radialGradient stop clipPath mask title text tspan use'.split(' '));
const attributes=new Set('viewBox d fill fill-rule clip-rule stroke stroke-width stroke-linecap stroke-linejoin stroke-dasharray stroke-dashoffset x y x1 y1 x2 y2 cx cy r rx ry width height points transform preserveAspectRatio xmlns offset stop-color stop-opacity gradientUnits gradientTransform id src alt aria-label title'.split(' '));
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const sha=s=>createHash('sha256').update(s).digest('hex');
const bad=message=>Object.assign(new Error(message),{status:400});
export async function addCapture(data,{root,store,backend,artifact}) {
  if(!data||typeof data.title!=='string'||!data.title.trim()||data.title.length>200||typeof data.route!=='string'||data.route.length>2048||!data.route.startsWith('/')||!Array.isArray(data.nodes)||!data.nodes.length||![data.width,data.height].every(n=>Number.isInteger(n)&&n>=40&&n<=8000))throw bad('设计稿内容或尺寸无效。');
  const assets=new Map(),warnings=Array.isArray(data.warnings)?data.warnings.filter(w=>typeof w==='string').slice(0,20):[],assetStyles=[],captureId=randomUUID().slice(0,8);let nodes=0;
  let fontCss='';
  if(data.fonts!==undefined&&(!Array.isArray(data.fonts)||data.fonts.length>12))throw bad('字体数量无效。');
  for(const f of data.fonts??[]){
    if(!f||typeof f.family!=='string'||!/^[\w -]{1,100}$/.test(f.family)||!['normal','italic','oblique'].includes(f.style)||!/^\d{1,4}( \d{1,4})?$/.test(f.weight)||typeof f.base64!=='string'||f.base64.length>2000000)throw bad('字体描述无效。');
    const bytes=Buffer.from(f.base64,'base64'),signature=bytes.subarray(0,4).toString(),ext=signature==='wOF2'?'woff2':signature==='wOFF'?'woff':null;
    if(!ext)throw bad('仅支持 WOFF/WOFF2 字体。');
    const temp=await mkdtemp(path.join(tmpdir(),'prototype-font-'));
    try{const filename=path.join(temp,'font.'+ext);await writeFile(filename,bytes);const {stdout}=await exec(process.execPath,[artifact,'upload',store,filename],{timeout:20000,maxBuffer:1048576});const url=JSON.parse(stdout).url;fontCss+=`@font-face{font-family:"${f.family}";font-style:${f.style};font-weight:${f.weight};font-display:block;src:url("${url}") format("${ext}")}\n`;}
    finally{await rm(temp,{recursive:true,force:true});}
  }
  async function asset(value) {
    if(value.startsWith('#'))return value;
    if(assets.has(value))return assets.get(value);
    if(assets.size>=64)throw bad('单次最多导入 64 个资源。');
    assets.set(value,'');let result='';
    try{
      const url=new URL(value,data.origin||'http://prototype.local');
      if(url.origin!==(data.origin||'http://prototype.local'))throw new Error('外部资源');
      const pathname=decodeURIComponent(url.pathname);
      if(pathname.includes('\\')||pathname.split('/').some(p=>p.startsWith('.')))throw new Error('隐藏或父目录');
      const file=await realpath(path.resolve(root,'.'+pathname));if(!file.startsWith(root+path.sep))throw new Error('目录外资源');
      const {stdout}=await exec(process.execPath,[artifact,'upload',store,file],{timeout:20000,maxBuffer:1048576});result=JSON.parse(stdout).url;
    }catch{warnings.push('未导入资源：'+value.slice(0,180));}
    assets.set(value,result);return result;
  }
  async function css(value) {
    if(typeof value!=='string'||value.length>10000||/[<>{}\u0000-\u0008]|expression\s*\(|javascript:/i.test(value))throw bad('设计样式无效。');
    let out='',at=0;
    for(const m of value.matchAll(/url\(\s*(["']?)(.*?)\1\s*\)/gi)){out+=value.slice(at,m.index);const url=await asset(m[2]);out+=url?'url("'+url+'")':'none';at=m.index+m[0].length;}
    return out+value.slice(at);
  }
  async function render(node,depth=0) {
    if(++nodes>6000||depth>70)throw bad('设计稿元素过多或嵌套过深。');
    if(typeof node==='string')return escape(node).replaceAll('{{','&#123;&#123;');
    if(!node||!tags.has(node.tag)||!Array.isArray(node.children)||!node.attributes||!node.style)throw bad('设计稿包含不支持的元素'+(typeof node?.tag==='string'?'：'+node.tag.slice(0,50):'')+'。');
    const props=[];
    for(const [key,value] of Object.entries(node.attributes)){
      if(!attributes.has(key)||typeof value!=='string'||value.length>100000)throw bad('设计稿属性无效。');
      const v=key==='src'?await asset(value):value;
      if(v)props.push(`${key}="${escape(v)}"`);
    }
    const styles=[],urls=[];
    for(const [key,value] of Object.entries(node.style)){if(!/^[a-z][a-z-]{0,60}$/.test(key))throw bad('设计样式名称无效。');const v=await css(value);(/url\(/i.test(v)?urls:styles).push(key+':'+v);}
    if(urls.length){const name='prototype-'+captureId+'-'+assetStyles.length;props.push('class="'+name+'"');assetStyles.push('.'+name+'{'+urls.join(';')+'}');}
    props.push('style="'+escape(styles.join(';'))+'"');
    const open='<'+node.tag+' '+props.join(' ')+'>';
    if(['img','br','hr'].includes(node.tag))return open;
    let content='';for(const child of node.children)content+=await render(child,depth+1);
    return open+content+'</'+node.tag+'>';
  }
  let markup='';for(const node of data.nodes)markup+=await render(node);
  const background=await css(data.background||'#fff'), file='Page-'+captureId+'.dc.html';
  if(/url\(/i.test(background))throw bad('画板背景应使用颜色值。');
  const source={url:data.route,title:data.title,language:String(data.language??'en').slice(0,30),theme:String(data.theme??'light').slice(0,30),capturedAt:new Date().toISOString(),editableSnapshot:true};
  const html=`<!doctype html>\n<html lang="${escape(source.language)}"><head><meta charset="utf-8"><title>${escape(data.title)}</title><script src="./support.js"></script></head><body><x-dc><helmet><style>${fontCss}${assetStyles.join('\n')}body{margin:0}a{color:inherit}a:hover{color:inherit}</style></helmet><div style="position:relative;width:${data.width}px;min-height:${data.height}px;overflow:hidden;box-sizing:border-box;background:${escape(background)}">${markup}</div></x-dc><script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":${data.width},"height":${data.height}}}'>class Component extends DCLogic {renderVals(){return {};}}</script></body></html>\n`;
  const origin=new URL(backend.url).origin;
  for(let attempt=0;attempt<3;attempt++){
    const original=await readFile(path.join(store,'project/canvas.json'),'utf8'),index=JSON.parse(original);
    const page='p-'+sha(data.route+'\0'+data.title).slice(0,12);
    index.title=path.basename(root)+' · 可编辑设计稿';index.pages??=[];
    if(!index.pages.some(p=>p.id===page))index.pages.push({id:page,name:data.title.slice(0,80)});
    const peers=Object.values(index.boards).filter(b=>b.page===page),x=peers.length?Math.max(...peers.map(b=>b.x+b.w))+80:0;
    index.boards[file]={x,y:0,w:data.width,h:data.height,title:data.title+' · '+data.width+'×'+data.height,page,prototypeSource:source};index.order.push(file);index.launch={view:'canvas',page};
    const entry=(value,ifMatch)=>({base64:Buffer.from(value).toString('base64'),contentType:'text/plain',ifMatch});
    const response=await fetch(new URL('__deck/publish',backend.url),{method:'POST',headers:{'Content-Type':'application/json',Origin:origin},body:JSON.stringify({files:{'project/canvas.json':entry(JSON.stringify(index,null,2)+'\n',sha(original)),['project/'+file]:entry(html,null)}})});
    if(response.status===409)continue;
    if(!response.ok)throw Object.assign(new Error('设计稿未保存，请重试。'),{status:502});
    return {editorUrl:backend.url,file,page,warnings,source};
  }
  throw Object.assign(new Error('画布刚被其他窗口修改，请重试；已有设计稿已保留。'),{status:409});
}
