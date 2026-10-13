// 固定上游的实际运行与协议样本；不修改 reference。
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const task = __dirname;
const isolated = path.join(task, '.cache/js-baseline');
const source = path.resolve(task, '../../../reference/js-junglebus');
const ts = require(path.join(isolated, 'node_modules/typescript'));
const pb = require(path.join(isolated, 'node_modules/protobufjs'));
const {WebSocketServer} = require(path.join(isolated, 'node_modules/ws'));
const compiled = path.join(isolated, 'compiled');
fs.mkdirSync(compiled, {recursive:true});
for (const name of ['index', 'interface', 'subscription', 'protobuf']) {
  const input = fs.readFileSync(path.join(source, 'src', name+'.ts'), 'utf8');
  const output = ts.transpileModule(input, {compilerOptions:{module:ts.ModuleKind.CommonJS, target:ts.ScriptTarget.ES2020, esModuleInterop:true}});
  fs.writeFileSync(path.join(compiled, name+'.js'), output.outputText);
}
const {JungleBusClient} = require(path.join(compiled, 'index'));
const {ProtobufRoot} = require(path.join(compiled, 'protobuf'));
const schemaFile = path.join(isolated, 'node_modules/centrifuge/build/protobuf/client.proto.json');
const schema = JSON.parse(fs.readFileSync(schemaFile));
const outer = pb.Root.fromJSON(schema);
const Command = outer.lookupType('protocol.Command');
const Reply = outer.lookupType('protocol.Reply');
const Message = ProtobufRoot.lookupType('Transaction');
const Control = ProtobufRoot.lookupType('ControlResponse');
let checks = 0;
function check(name, actual, expected) { assert.deepEqual(actual, expected, name); checks++; }
const timeout = (ms=3000) => new Promise((_,reject) => {const t=setTimeout(()=>reject(new Error('基线超时')),ms);t.unref();});
const fixture = {id:'a'.repeat(64),block_hash:'b'.repeat(64),block_height:120,block_index:3,block_time:1710000000,transaction:Buffer.from([0,255,1]),merkle_proof:Buffer.from([10,11])};
const control = {statusCode:200,status:'done',message:'block done',block:120,transactions:1};
function encodePub(protocol, value, isControl=false) {
  if(protocol==='protobuf') return (isControl?Control:Message).encode(value).finish();
  if(isControl) return value;
  return {...value, transaction:value.transaction.toString('base64'),merkle_proof:value.merkle_proof.toString('base64')};
}
async function networkCase(protocol, lite) {
  const requests=[];
  const commandsSeen=[];
  const server=http.createServer(async(req,res)=>{
    requests.push(req.url);
    let input='';for await(const chunk of req) input+=chunk;
    if(req.url.endsWith('/bin')) {res.end(Buffer.from([222,173,190,239]));return;}
    res.setHeader('content-type','application/json');
    if(req.url==='/v1/user/login'||req.url==='/v1/user/subscription-token'||req.url==='/v1/user/refresh-token') {
      if(req.url.includes('refresh')) check('刷新使用 token 头',req.headers.token,'fixture-token');
      res.end(JSON.stringify({token:'fixture-token'}));
    } else if(req.url.includes('/transaction/get/missing')) {res.statusCode=404;res.end('{}');}
    else if(req.url.includes('block_header/list')) res.end(JSON.stringify([{height:120,hash:'b'.repeat(64)}]));
    else if(req.url.includes('block_header/get')) res.end(JSON.stringify({height:120,hash:'b'.repeat(64)}));
    else if(req.url.includes('/address/')) res.end(JSON.stringify([{id:'address-reference',address:'fixture',transaction_id:fixture.id,unknown:'retained'}]));
    else res.end(JSON.stringify({id:fixture.id,transaction:'deadbeef'}));
  });
  const wss=new WebSocketServer({server});
  let receivedConnect=false;
  wss.on('connection', socket=>{
    const subscribed=[];
    function send(reply) {socket.send(protocol==='protobuf'?Reply.encodeDelimited(reply).finish():JSON.stringify(reply));}
    socket.on('message', raw=>{
      const commands=[];
      if(protocol==='protobuf') {const reader=pb.Reader.create(raw);while(reader.pos<reader.len)commands.push(Command.decodeDelimited(reader));}
      else commands.push(...raw.toString().split('\n').map(JSON.parse));
      for(const cmd of commands) {
        commandsSeen.push(cmd.connect?'connect':cmd.subscribe?cmd.subscribe.channel:cmd.unsubscribe?'unsubscribe':'other');
        if(cmd.connect) {receivedConnect=true;send({id:cmd.id,connect:{client:'fixture-client'}});}
        else if(cmd.subscribe) {
          subscribed.push(cmd.subscribe.channel);
          send({id:cmd.id,subscribe:{recoverable:true,epoch:'fixture-epoch',offset:0}});
          if(subscribed.length===3) setTimeout(()=>{
            const block=subscribed.find(x=>/:120$/.test(x));
            const mempool=subscribed.find(x=>x.endsWith(':mempool'));
            const ctl=subscribed.find(x=>x.endsWith(':control'));
            check('控制通道不随 Lite 改前缀',ctl,'query:fixture:control');
            check('区块通道',block,`${lite?'lite':'query'}:fixture:120`);
            send({push:{channel:block,pub:{offset:1,data:encodePub(protocol,{...fixture,transaction:Buffer.alloc(0),merkle_proof:Buffer.alloc(0)})}}});
            send({push:{channel:ctl,pub:{offset:1,data:encodePub(protocol,control,true)}}});
            send({push:{channel:mempool,pub:{offset:1,data:encodePub(protocol,{...fixture,transaction:Buffer.from([0,255,1]),merkle_proof:Buffer.alloc(0)})}}});
          },10);
        } else if(cmd.unsubscribe) send({id:cmd.id,unsubscribe:{}});
        else if(cmd.publish) send({id:cmd.id,publish:{}});
      }
    });
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const client=new JungleBusClient(`http://127.0.0.1:${server.address().port}`,{protocol});
  const received=[];
  let complete;
  const done=new Promise(resolve=>{complete=resolve;});
  const record=(kind,value)=>{received.push([kind,value]);if(received.length===3)complete();};
  const subscription=await client.Subscribe('fixture',120,tx=>record('block',tx),message=>record('control',message),err=>{throw new Error(JSON.stringify(err));},tx=>record('mempool',tx),lite);
  try {
    await Promise.race([done,timeout()]).catch(error=>{error.message+=JSON.stringify({protocol,lite,requests,commandsSeen,received:received.map(x=>x[0])});throw error;});
    check('实际 JS 连接成功',receivedConnect,true);
    check('报告高度',subscription.GetCurrentBlock(),120);
    check('区块正文补取',received.find(x=>x[0]==='block')[1].transaction,lite?'':'deadbeef');
    check('Mempool hex 与缺失证明',[received.find(x=>x[0]==='mempool')[1].transaction,received.find(x=>x[0]==='mempool')[1].merkle_proof],['00ff01','']);
    check('Lite 不补取',requests.filter(x=>x.endsWith('/bin')).length,lite?0:1);
    check('首次连接先刷新',requests.includes('/v1/user/refresh-token'),true);
    check('匿名 Token',requests.includes('/v1/user/subscription-token'),true);
    check('登录',await client.Login('fixture','fixture'),null);
    check('REST 交易', (await client.GetTransaction(fixture.id)).transaction,'deadbeef');
    check('REST 区块头', (await client.GetBlockHeader(120)).height,120);
    check('REST 区块列表', (await client.GetBlockHeaders(120,2)).length,1);
    check('REST 地址引用',(await client.GetAddressTransactions('fixture'))[0].unknown,'retained');
    check('REST 地址详情',(await client.GetAddressTransactionDetails('fixture'))[0].unknown,'retained');
    check('上游非 200 空值',await client.GetTransaction('missing'),null);
    check('最近错误',!!client.GetLastError(),true);
  } finally {
    subscription.UnSubscribe();client.Disconnect();
    for(const socket of wss.clients)socket.terminate();
    await new Promise(resolve=>wss.close(resolve));await new Promise(resolve=>server.close(resolve));
  }
}
async function main(){
  for(const protocol of ['json','protobuf'])for(const lite of [false,true])await networkCase(protocol,lite);
  check('默认 JSON',new JungleBusClient('fixture').client.protocol,'json');
  check('默认 TLS',new JungleBusClient('fixture').client.useSSL,true);
  check('HTTP 明文',new JungleBusClient('http://fixture').client.useSSL,false);
  const {ProtobufEncoder}=require(path.join(isolated,'node_modules/centrifuge/build/protobuf'));
  const original=new ProtobufEncoder().encodeCommands([{id:1,publish:{channel:'query:fixture:120',data:{cmd:'pause'}}}]);
  check('上游 Protobuf pause 对象被编码为空 bytes',Command.decodeDelimited(original).publish.data.length,0);
  const maxMessage=Message.fromObject({...fixture,block_height:4294967295,block_index:'18446744073709551615'});
  const maxBytes=Message.encode(maxMessage).finish();
  check('uint64 字节保真',Message.decode(maxBytes).block_index.toString(),'18446744073709551615');
  const commands=[{id:1,connect:{token:'fixture-token',name:'java'}},{id:2,subscribe:{channel:'query:fixture:120'}},{id:3,unsubscribe:{channel:'query:fixture:120'}},{id:4,publish:{channel:'query:fixture:120',data:{cmd:'pause'}}},{id:5,publish:{channel:'query:fixture:120',data:{cmd:'start'}}},{id:6,refresh:{token:'next-token'}},{},{id:7,subscribe:{channel:'query:fixture:120',recover:true,epoch:'fixture-epoch',offset:'9'}}];
  const vectors=commands.map(command=>{
    const wire=structuredClone(command);
    if(wire.publish)wire.publish.data=Buffer.from(JSON.stringify(wire.publish.data));
    return {command,protobufHex:Buffer.from(Command.encodeDelimited(wire).finish()).toString('hex')};
  });
  const golden={schemaSha256:crypto.createHash('sha256').update(fs.readFileSync(schemaFile)).digest('hex'),commands:vectors,transactions:[{protobufHex:Buffer.from(Message.encode(fixture).finish()).toString('hex'),json:encodePub('json',fixture),expectedHex:'00ff01',expectedProof:'0a0b'},{protobufHex:Buffer.from(maxBytes).toString('hex'),json:{...encodePub('json',fixture),block_height:4294967295,block_index:'18446744073709551615'},expectedHex:'00ff01',expectedProof:'0a0b'}],control:{protobufHex:Buffer.from(Control.encode(control).finish()).toString('hex'),json:control},intentionalDifferences:['protobuf pause/start use UTF-8 JSON bytes; upstream encodes plain object as empty bytes','await asynchronous application callback','only subscribe requested mempool']};
  const fixtures=path.join(task,'fixtures');fs.mkdirSync(fixtures,{recursive:true});
  for(const[name,value]of [['wire.json',golden],['client.proto.json',schema]]) {
    const target=path.join(fixtures,name);const text=JSON.stringify(value,null,2)+'\n';
    if(fs.existsSync(target))assert.equal(fs.readFileSync(target,'utf8'),text,'固定样本变化需审查');else fs.writeFileSync(target,text);
  }
  fs.mkdirSync(path.join(task,'.cache/evidence'),{recursive:true});
  fs.writeFileSync(path.join(task,'.cache/evidence/js-baseline.json'),JSON.stringify({checks,passed:true,protocols:['json','protobuf'],liteModes:[false,true],schemaSha256:golden.schemaSha256},null,2)+'\n');
  console.log(`JS 基线通过：${checks} 项断言，双格式 × 普通/Lite，实际 HTTP/WebSocket，固定协议样本已核对。`);
}
main().catch(error=>{console.error(error);process.exitCode=1;});
