#!/usr/bin/env node
// 独立静态预览；评论存储、回复和状态处理复用新版 Artifact 服务。
import http from 'node:http';
import {createReadStream} from 'node:fs';
import {mkdir, readFile, realpath, stat, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {Readable} from 'node:stream';

const exec = promisify(execFile);
const here = path.dirname(fileURLToPath(import.meta.url));
const artifact = path.resolve(here, '../artifact.mjs');
const api = '/__prototype-review';
const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.gif':'image/gif','.ico':'image/x-icon','.woff2':'font/woff2','.woff':'font/woff','.mp4':'video/mp4','.webm':'video/webm','.mp3':'audio/mpeg','.wav':'audio/wav','.pdf':'application/pdf'};
const inside = (root, file) => file === root || file.startsWith(root + path.sep);
export const commentStore = (root, store) => path.resolve(store ?? path.join(root, '.prototype-review'));
function json(res, status, value) {res.writeHead(status,{'Content-Type':'application/json; charset=utf-8'}); res.end(JSON.stringify(value));}
async function jsonFile(file, fallback) {
  try {return JSON.parse(await readFile(file,'utf8'));}
  catch (e) {if (e.code === 'ENOENT') return fallback; throw e;}
}
async function body(req) {
  const chunks=[]; let size=0;
  for await (const chunk of req) {
    size+=chunk.length;
    if (size>65536) throw Object.assign(new Error('评论请求过大。'),{status:413});
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}
async function prepare(root, store) {
  await mkdir(path.join(store,'project'),{recursive:true});
  const index=path.join(store,'project/canvas.json');
  const existing=await jsonFile(index,null);
  if (existing && existing.sourcePrototype !== root) throw new Error('评论目录已绑定其他原型，请指定其他 --store。');
  if (!existing) {
    await writeFile(index,JSON.stringify({v:3,title:'原型页面评论',createdOnFiles:{v:1,at:new Date().toISOString()},boards:{},order:[],pages:[],notes:{},designSystems:[],sourcePrototype:root},null,2)+'\n',{flag:'wx'});
    await writeFile(path.join(store,'.gitignore'),'*\n',{flag:'wx'});
  }
  const {stdout}=await exec(process.execPath,[artifact,'open',store,'--port','0'],{timeout:20000,maxBuffer:1048576});
  return JSON.parse(stdout);
}

export async function startReview(givenRoot,{port=4316,store:givenStore}={}) {
  const root=await realpath(path.resolve(givenRoot));
  if (!(await stat(path.join(root,'index.html'))).isFile()) throw new Error('请指定包含 index.html 的已构建原型目录。');
  if (!Number.isInteger(port)||port<0||port>65535) throw new Error('--port 必须是 0–65535 的整数。');
  const version=await jsonFile(path.join(root,'version.json'),null), pkg=await jsonFile(path.join(root,'package.json'),{});
  const store=commentStore(root,givenStore), backend=await prepare(root,store);
  const backendOrigin=new URL(backend.url).origin;
  let actualPort=0;
  const server=http.createServer(async(req,res)=>{
    res.setHeader('Cache-Control','no-store'); res.setHeader('X-Content-Type-Options','nosniff');
    try {
      const hosts=[`127.0.0.1:${actualPort}`,`localhost:${actualPort}`];
      if (!hosts.includes(req.headers.host)) return json(res,403,{message:'预览仅允许本机访问。'});
      const reading=req.method==='GET'||req.method==='HEAD';
      if (!reading&&(req.headers.origin ? req.headers.origin!==`http://${req.headers.host}` : ['cross-site','same-site'].includes(req.headers['sec-fetch-site']))) {
        req.resume(); return json(res,403,{message:'不接受跨站评论请求。'});
      }
      const url=new URL(req.url,`http://${req.headers.host}`);
      if (url.pathname===api+'/meta') {
        if (!reading) return json(res,405,{message:'不支持该操作。'});
        return json(res,200,{project:path.basename(root),version:version?.prototypeVersion??pkg.version??null});
      }
      if (url.pathname===api+'/client.js') {
        if (!reading) return json(res,405,{message:'不支持该操作。'});
        res.writeHead(200,{'Content-Type':'text/javascript; charset=utf-8'});
        return res.end(req.method==='HEAD'?undefined:await readFile(path.join(here,'client.js')));
      }
      const comments=api+'/comments';
      if (url.pathname===comments||url.pathname.startsWith(comments+'/')) {
        const target=new URL('__comments'+url.pathname.slice(comments.length)+url.search,backend.url);
        const controller=new AbortController(); res.on('close',()=>controller.abort());
        const upstream=await fetch(target,{method:req.method,headers:{'Content-Type':'application/json',Origin:backendOrigin},body:reading?undefined:await body(req),signal:controller.signal});
        res.writeHead(upstream.status,{'Content-Type':upstream.headers.get('content-type')??'application/json'});
        if (req.method==='HEAD'||!upstream.body) return res.end();
        Readable.fromWeb(upstream.body).on('error',()=>res.destroy()).pipe(res); return;
      }
      if (!reading) {req.resume(); return json(res,405,{message:'不支持该操作。'});}
      const pathname=decodeURIComponent(url.pathname);
      if (pathname.includes('\\')||pathname.split('/').some(p=>p.startsWith('.'))) return json(res,403,{message:'不能访问隐藏目录或父目录。'});
      let file=await realpath(path.resolve(root,'.'+pathname));
      if (!inside(root,file)) return json(res,403,{message:'文件不属于当前原型。'});
      if ((await stat(file)).isDirectory()) file=await realpath(path.join(file,'index.html'));
      if (!inside(root,file)) return json(res,403,{message:'文件不属于当前原型。'});
      const type=mime[path.extname(file).toLowerCase()]??'application/octet-stream';
      if (type.startsWith('text/html')) {
        const original=await readFile(file,'utf8'), script=`<script defer src="${api}/client.js"></script>`;
        const output=/<\/body\s*>/i.test(original)?original.replace(/<\/body\s*>/i,script+'</body>'):original+script;
        res.writeHead(200,{'Content-Type':type}); return res.end(req.method==='HEAD'?undefined:output);
      }
      res.writeHead(200,{'Content-Type':type,'Content-Length':(await stat(file)).size});
      if (req.method==='HEAD') return res.end();
      createReadStream(file).on('error',()=>res.destroy()).pipe(res);
    } catch(e) {
      if (res.destroyed) return;
      if (res.headersSent) return res.destroy();
      const status=e.status??(['ENOENT','ENOTDIR'].includes(e.code)?404:e instanceof URIError?400:502);
      json(res,status,{message:status===404?'文件不存在。':status===502?'评论服务暂时不可用，请保留文字并重试。':e.message});
    }
  });
  try {
    await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',resolve);});
    actualPort=server.address().port;
  } catch(e) {
    if (!backend.reused) await exec(process.execPath,[artifact,'stop',store]).catch(()=>{});
    throw e;
  }
  return {server,root,store,url:`http://127.0.0.1:${actualPort}/`,backend,async close(){
    server.closeAllConnections(); await new Promise(resolve=>server.close(resolve));
    if (!backend.reused) await exec(process.execPath,[artifact,'stop',store]).catch(()=>{});
  }};
}

async function main(args) {
  if (!args.length||args.includes('--help')) {
    console.log('用法：node server.mjs <已构建原型目录> [--port 4316] [--store 评论目录]\n读取：node server.mjs comments <原型目录> [--all | --wait]'); return;
  }
  if (args[0]==='comments') {
    if (!args[1]) throw new Error('请指定原型目录。');
    const forwarded=args.slice(2), index=forwarded.indexOf('--store');
    const custom=index<0?undefined:forwarded.splice(index,2)[1];
    if(index>=0&&!custom)throw new Error('--store 缺少评论目录。');
    const root=await realpath(path.resolve(args[1]));
    const child=execFile(process.execPath,[artifact,'comments',commentStore(root,custom),...forwarded],{maxBuffer:4194304});
    child.stdout.pipe(process.stdout); child.stderr.pipe(process.stderr);
    await new Promise((resolve,reject)=>{child.on('error',reject);child.on('exit',code=>code===0?resolve():reject(new Error('读取评论失败。')));}); return;
  }
  const options={};
  for(let i=1;i<args.length;i+=2) {
    if(args[i]==='--port'&&args[i+1]!==undefined) options.port=Number(args[i+1]);
    else if(args[i]==='--store'&&args[i+1]) options.store=args[i+1];
    else throw new Error(`未知或不完整的参数：${args[i]}`);
  }
  const running=await startReview(args[0],options);
  console.log(JSON.stringify({url:running.url,prototype:running.root,comments:running.store},null,2));
  let closing=false;
  for(const signal of ['SIGINT','SIGTERM']) process.on(signal,async()=>{if(closing)return;closing=true;await running.close();process.exit(0);});
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href) {
  main(process.argv.slice(2)).catch(e=>{console.error(e.message);process.exitCode=1;});
}
