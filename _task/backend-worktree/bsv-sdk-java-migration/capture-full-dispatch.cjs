// 全量运行的探针分派：按当前执行的测试文件装对应探针，并把探针需要的原始轨迹／冻结语料
// 环境变量指向本轮运行目录。查不到的文件只记 unmapped-files.jsonl，不中断 Jest。
//
// 探针条目除 outputs／corpus／values 外还支持三个全量运行专用字段（由 full-run-overrides.json
// 注入，静态解析不出来的旧管线局部才需要）：
//   envOverrides 额外环境变量（例如把 EVIDENCE_INPUT_PLAN 指到本轮复制的局部冻结计划目录）
//   fork      true 表示该探针会替换 global.expect，必须排在 capture-parity.cjs 之后装载，
//             否则这些文件的原断言不会进入本轮共享断言轨迹；
//   expect    "replace" 表示该探针要把 global.expect 装成自己的实现（默认行为），
//             "wrap" 表示它是在已有层外面加一层（例如按行号记录入口引用），
//             装载时期望已有 global.expect 作为下一层。
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

function applyEnv(item) {
  // 输出轨迹先落到本轮运行目录；语料与固定取值按分派表原样注入。
  // 整轮共享的轨迹/日志环境变量（断言轨迹、网络日志）不能被逐文件覆盖，除非该条目显式
  // 指定了私有轨迹文件（outputs 里出现同一个变量）：否则这些文件的断言行会落到各自文件里，
  // 全量断言转换读不到 → strict 失败。
  const SHARED_ENVS = new Set(['MIGRATION_PARITY_JAVA_OUTPUT', 'MIGRATION_NETWORK_LOG'])
  for (const [env, name] of Object.entries(item.outputs || {})) {
    if (SHARED_ENVS.has(env)) continue
    process.env[env] = path.join(runDir, name)
  }
  for (const [env, value] of Object.entries(item.corpus || {})) process.env[env] = value
  for (const [env, value] of Object.entries(item.values || {})) process.env[env] = String(value)
  for (const [env, value] of Object.entries(item.envOverrides || {})) {
    process.env[env] = String(value).replaceAll('{runDir}', runDir)
  }
}

/** 装载单个探针；失败只记账，不中断 Jest。 */
function install(item) {
  const probePath = path.isAbsolute(item.probe) ? item.probe : path.join(__dirname, item.probe)
  if (!fs.existsSync(probePath)) {
    record(ledger, { file: relative, local: item.local, probe: item.probe, reason: 'probe-missing' })
    return false
  }
  applyEnv(item)
  try {
    require(probePath)
    return true
  } catch (error) {
    record(ledger, {
      file: relative, local: item.local, probe: item.probe, reason: 'probe-threw',
      error: String((error && error.message) || error)
    })
    return false
  }
}

if (!entry) {
  record(ledger, { file: relative, absPath: testPath, reason: 'not-in-probe-table' })
} else {
  const probes = (Array.isArray(entry.probes) && entry.probes.length ? entry.probes : [entry])
    .filter(item => item && item.probe)
  // 普通探针先装（它们会替换 global.expect），fork 探针随后装：fork 外层保留的
  // global.expect 是替换后的实现，于是替换层仍在链上，原断言照样进入共享轨迹文件。
  const ordered = [...probes.filter(item => !item.fork), ...probes.filter(item => item.fork)]
  const installed = []
  for (const item of ordered) {
    if (install(item)) installed.push(item.probe)
  }
  record(dispatched, { file: relative, locals: probes.map(item => item.local), installed })
}
