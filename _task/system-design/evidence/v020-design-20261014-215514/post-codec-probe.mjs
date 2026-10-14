// 只构造内存脚本，不连接钱包、不签名、不广播、不修改仓库依赖。
// 从工作区根运行：node _task/system-design/evidence/v020-design-20261014-215514/post-codec-probe.mjs
import { BSocial } from '../../../fronted-worktree/ownword-v0.1.0/own-word-web/node_modules/@1sat/templates/dist/index.js';

const input = {app: 'ownword', type: 'post', content: '# 中文\r\n', mediaType: 'text/markdown', encoding: 'utf-8'};
const script = await BSocial.createPost(input);
const fields = script.chunks.filter(chunk => chunk.data).map(chunk => Buffer.from(chunk.data).toString('utf8'));
console.log(JSON.stringify({package: '@1sat/templates@0.0.37', input, fields, walletCalled: false, broadcastCalled: false}, null, 2));
