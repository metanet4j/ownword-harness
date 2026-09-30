// 基线测试可替换为自己的 mock；任何落到真实平台网络的调用都记录并拒绝。
const fs = require('node:fs')
const log = process.env.MIGRATION_NETWORK_LOG
if (!log) throw new Error('离线测试必须指定 MIGRATION_NETWORK_LOG')

function denied(transport, target) {
  fs.appendFileSync(log, JSON.stringify({ transport, target: String(target), test: globalThis.expect?.getState?.().currentTestName ?? null }) + '\n')
  return new Error(`迁移基线禁止真实网络调用：${transport} ${target}`)
}

if (typeof globalThis.fetch === 'function') {
  globalThis.fetch = async input => {
    const target = String(input?.url ?? input)
    const state = globalThis.expect?.getState?.() ?? {}
    // 上游明确要求“通过参数校验后因没有钱包而拒绝”；固定为无服务环境。
    let fixture
    if (state.testPath?.endsWith('/src/wallet/__tests/WalletClient.additional.test.ts') &&
        state.currentTestName === 'WalletClient – signAction validation does NOT throw for a minimal valid signAction call structure (gets past validation)' &&
        ['http://localhost:3301/getVersion', 'https://localhost:2121/getVersion', 'http://localhost:3321/getVersion'].includes(target)) {
      fixture = 'wallet-unavailable'
    }
    // 该用例只断言返回 thenable，并显式捕获网络失败；不需要真实区块头。
    if (state.testPath?.endsWith('/src/transaction/chaintrackers/__tests/DefaultChainTracker.test.ts') &&
        state.currentTestName === 'defaultChainTracker WhatsOnChain defaults returns a tracker that responds to isValidRootForHeight as a function' &&
        target === 'https://api.whatsonchain.com/v1/bsv/main/block/0/header') {
      fixture = 'chaintracker-unavailable'
    }
    if (fixture) {
      fs.appendFileSync(log.replace(/\.jsonl$/, '.fixtures.jsonl'), JSON.stringify({ fixture, target, test: state.currentTestName }) + '\n')
      throw new TypeError('fetch failed', { cause: { code: 'ECONNREFUSED' } })
    }
    throw denied('fetch', target)
  }
}

require('node:net').Socket.prototype.connect = function () {
  // Node 连接选项可能持有循环引用；拒绝记录不依赖这些选项能否序列化。
  throw denied('socket', 'Socket.connect')
}
