// 全量运行的探针分派：按当前执行的测试文件装对应探针，并把探针需要的原始轨迹／冻结语料
// 环境变量指向本轮运行目录。查不到的文件只记 unmapped-files.jsonl，不中断 Jest。
'use strict'
const fs = require('node:fs')
const path = require('node:path')

const runDir = process.env.MIGRATION_FULL_RUN_DIR
if (!runDir) throw new Error('缺少 MIGRATION_FULL_RUN_DIR；全量 TS 采集必须指定本轮运行目录')
const tablePath = process.env.MIGRATION_FULL_PROBES || path.join(__dirname, 'full-run-probes.json')
if (!fs.existsSync(tablePath)) throw new Error('缺少探针分派表：' + tablePath)
const table = JSON.parse(fs.readFileSync(tablePath, 'utf8'))
const ledger = path.join(runDir, 'unmapped-files.jsonl')
const dispatched = path.join(runDir, 'dispatched-files.jsonl')

function record(file, row) {
  fs.appendFileSync(file, JSON.stringify(row) + '\n')
}

const state = typeof expect !== 'undefined' && expect.getState ? expect.getState() : {}
const testPath = String(state.testPath || '')
const relative = testPath.includes('/src/')
  ? 'src/' + testPath.split('/src/').pop()
  : path.basename(testPath)
const entry = table.files && table.files[relative]
if (!entry) {
  record(ledger, { file: relative, absPath: testPath, reason: 'not-in-probe-table' })
} else {
  const probes = Array.isArray(entry.probes) && entry.probes.length ? entry.probes : [entry]
  const installed = []
  for (const item of probes) {
    if (!item || !item.probe) continue
    const probePath = path.isAbsolute(item.probe) ? item.probe : path.join(__dirname, item.probe)
    if (!fs.existsSync(probePath)) {
      record(ledger, { file: relative, local: item.local, probe: item.probe, reason: 'probe-missing' })
      continue
    }
    // 输出轨迹先落到本轮运行目录；语料与固定取值按分派表原样注入。
    for (const [env, name] of Object.entries(item.outputs || {})) {
      process.env[env] = path.join(runDir, name)
    }
    for (const [env, value] of Object.entries(item.corpus || {})) process.env[env] = value
    for (const [env, value] of Object.entries(item.values || {})) process.env[env] = String(value)
    try {
      require(probePath)
      installed.push(item.probe)
    } catch (error) {
      record(ledger, {
        file: relative, local: item.local, probe: item.probe, reason: 'probe-threw',
        error: String((error && error.message) || error)
      })
    }
  }
  record(dispatched, { file: relative, locals: probes.map(item => item.local), installed })
}
