// 固定上游的源码声明清点；只解析 TypeScript，不加载或执行被清点模块。
const fs = require('node:fs')
const path = require('node:path')
const { createHash } = require('node:crypto')
const { createRequire } = require('node:module')
const { execFileSync } = require('node:child_process')
const { isDeepStrictEqual } = require('node:util')
const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'workspace.json')))
const realSdk = path.resolve(__dirname, '../../..', config.upstream.path, config.upstream.packagePath)
const ts = createRequire(path.join(realSdk, 'package.json'))('typescript')
const sha = value => createHash('sha256').update(value).digest('hex')
const read = file => JSON.parse(fs.readFileSync(file))
const flag = (node, kind) => node.modifiers?.some(m => m.kind === kind) || false
const posix = file => file.split(path.sep).join('/')

function inventory(sdk, modules) {
  let files = modules.flatMap(module => fs.readdirSync(path.join(sdk, 'src', module), { recursive: true })
    .filter(file => file.endsWith('.ts') && !file.endsWith('.test.ts') && !file.split(path.sep).some(p => ['__tests', '__tests__'].includes(p)))
    .map(file => posix(path.join('src', module, file)))).sort()
  const hasRoot = fs.existsSync(path.join(sdk, 'mod.ts'))
  const program = ts.createProgram([...files, ...(hasRoot ? ['mod.ts'] : [])].map(f => path.join(sdk, f)), {
    target: ts.ScriptTarget.ESNext, module: ts.ModuleKind.NodeNext,
    moduleResolution: ts.ModuleResolutionKind.NodeNext, skipLibCheck: true, noEmit: true
  })
  // 测试目录可能被生产入口公开导出，所有真实依赖必须重新纳入。
  files = program.getSourceFiles().map(source => posix(path.relative(sdk, source.fileName)))
    .filter(file => file.startsWith('src/') && modules.includes(file.split('/')[1]) && file.endsWith('.ts')).sort()
  const checker = program.getTypeChecker()
  const entries = [], exports = [], byNode = new Map(), fileRecords = []
  for (const file of files) {
    const source = program.getSourceFile(path.join(sdk, file))
    const counts = new Map()
    const text = source.text
    const sourceText = node => node?.getText(source)
    const inferred = node => checker.typeToString(checker.getTypeAtLocation(node), node,
      ts.TypeFormatFlags.NoTruncation | ts.TypeFormatFlags.UseAliasDefinedOutsideCurrentScope)
    function add(node, name, kind, parent, callable = node) {
      const qualified = parent ? parent + '.' + name : name
      const key = `${kind}:${qualified}`
      const occurrence = (counts.get(key) || 0) + 1
      counts.set(key, occurrence)
      const location = source.getLineAndCharacterOfPosition(node.getStart(source))
      const end = source.getLineAndCharacterOfPosition(node.end)
      let signature = sourceText(node)
      if (node.body) signature = text.slice(node.getStart(source), node.body.getStart(source)).trim()
      else if (node.initializer) signature = text.slice(node.getStart(source), node.initializer.pos).replace(/=\s*$/, '').trim()
      if (ts.isClassDeclaration(node) || ts.isInterfaceDeclaration(node) || ts.isEnumDeclaration(node)) {
        signature = text.slice(node.getStart(source), node.members.pos).trim()
      }
      const parameters = callable.parameters?.map(p => ({
        name: sourceText(p.name), type: p.type ? sourceText(p.type) : inferred(p),
        optional: !!p.questionToken, rest: !!p.dotDotDotToken,
        ...(p.initializer ? { default: sourceText(p.initializer) } : {})
      }))
      const callableSignature = parameters ? checker.getSignatureFromDeclaration(callable) : undefined
      const entry = {
        id: `${file}#${key}:${occurrence}`, file, module: file.split('/')[1], name: qualified, kind,
        line: location.line + 1, column: location.character + 1, endLine: end.line + 1,
        visibility: flag(node, ts.SyntaxKind.PrivateKeyword) ? 'private' : flag(node, ts.SyntaxKind.ProtectedKeyword) ? 'protected' : 'public',
        static: flag(node, ts.SyntaxKind.StaticKeyword), readonly: flag(node, ts.SyntaxKind.ReadonlyKeyword),
        optional: !!node.questionToken, async: flag(callable, ts.SyntaxKind.AsyncKeyword),
        exportNames: [], signature, sourceSha256: sha(sourceText(node)),
        ...(parameters ? { parameters, returns: callable.type ? sourceText(callable.type) : callableSignature ? checker.typeToString(checker.getReturnTypeOfSignature(callableSignature), callable, ts.TypeFormatFlags.NoTruncation) : 'void' } : {}),
        ...(node.type ? { type: sourceText(node.type) } : {}),
        ...(node.initializer && !ts.isArrowFunction(node.initializer) && !ts.isFunctionExpression(node.initializer) ? { initializer: sourceText(node.initializer) } : {}),
        ...(node.heritageClauses ? { heritage: node.heritageClauses.map(sourceText) } : {})
      }
      // 留下显式失败位置；间接调用及状态变化仍须读固定源码，不能凭此声称完整行为分析。
      entry.throws = []
      function failures(child) {
        if (ts.isThrowStatement(child)) entry.throws.push({ line: source.getLineAndCharacterOfPosition(child.getStart(source)).line + 1, expression: sourceText(child.expression) })
        ts.forEachChild(child, failures)
      }
      if (!['class', 'interface', 'enum', 'type'].includes(kind)) failures(node)
      entries.push(entry)
      byNode.set(node, entry)
      return qualified
    }
    function member(node, parent) {
      const name = ts.isConstructorDeclaration(node) ? 'constructor' : node.name ? sourceText(node.name) : ts.isIndexSignatureDeclaration(node) ? '$index' : ts.isCallSignatureDeclaration(node) ? '$call' : ts.isConstructSignatureDeclaration(node) ? '$new' : '$anonymous'
      const kind = ts.isConstructorDeclaration(node) ? 'constructor' : ts.isGetAccessor(node) ? 'get' : ts.isSetAccessor(node) ? 'set' : ts.isMethodDeclaration(node) || ts.isMethodSignature(node) ? 'method' : ts.isEnumMember(node) ? 'enum-member' : 'property'
      add(node, name, kind, parent, node.initializer && (ts.isArrowFunction(node.initializer) || ts.isFunctionExpression(node.initializer)) ? node.initializer : node)
      if (ts.isConstructorDeclaration(node)) {
        for (const parameter of node.parameters) {
          if (parameter.modifiers?.some(m => [ts.SyntaxKind.PublicKeyword, ts.SyntaxKind.PrivateKeyword, ts.SyntaxKind.ProtectedKeyword, ts.SyntaxKind.ReadonlyKeyword].includes(m.kind))) {
            add(parameter, sourceText(parameter.name), 'parameter-property', parent)
          }
        }
      }
    }
    for (const node of source.statements) {
      if (ts.isClassDeclaration(node) || ts.isInterfaceDeclaration(node) || ts.isEnumDeclaration(node)) {
        const name = node.name?.text || 'default'
        const kind = ts.isClassDeclaration(node) ? 'class' : ts.isInterfaceDeclaration(node) ? 'interface' : 'enum'
        add(node, name, kind)
        for (const m of node.members) member(m, name)
      } else if (ts.isTypeAliasDeclaration(node)) {
        add(node, node.name.text, 'type')
      } else if (ts.isFunctionDeclaration(node)) {
        add(node, node.name?.text || 'default', 'function')
      } else if (ts.isVariableStatement(node)) {
        for (const declaration of node.declarationList.declarations) {
          const name = sourceText(declaration.name)
          const fn = declaration.initializer && (ts.isArrowFunction(declaration.initializer) || ts.isFunctionExpression(declaration.initializer))
          add(declaration, name, fn ? 'function-variable' : 'variable', undefined, fn ? declaration.initializer : declaration)
          if (declaration.initializer && ts.isObjectLiteralExpression(declaration.initializer)) {
            for (const m of declaration.initializer.properties) member(m, name)
          }
        }
      } else if (ts.isExportAssignment(node)) {
        add(node, node.isExportEquals ? 'export=' : 'default', 'export-assignment')
      } else if (ts.isModuleDeclaration(node)) {
        throw new Error(`尚未支持的命名空间声明：${file}:${node.name.getText(source)}`)
      }
    }
    fileRecords.push({ path: file, sha256: sha(text) })
  }
  // 编译器解析导出别名、export * 和 import * 命名空间，不按 index.ts 猜测公开范围。
  for (const file of [...files, ...(hasRoot ? ['mod.ts'] : [])]) {
    const source = program.getSourceFile(path.join(sdk, file))
    const symbol = checker.getSymbolAtLocation(source)
    if (!symbol) continue
    for (const exported of checker.getExportsOfModule(symbol)) {
      const target = exported.flags & ts.SymbolFlags.Alias ? checker.getAliasedSymbol(exported) : exported
      if (file === 'mod.ts' && !(target.declarations || []).some(d => files.includes(posix(path.relative(sdk, d.getSourceFile().fileName))))) continue
      const targets = []
      for (const declaration of target.declarations || []) {
        const entry = byNode.get(declaration)
        if (entry) {
          targets.push(entry.id)
          if (entry.file === file) entry.exportNames.push(exported.name)
        } else if (ts.isSourceFile(declaration)) targets.push('namespace:' + posix(path.relative(sdk, declaration.fileName)))
        else throw new Error(`未解析的导出 ${file}:${exported.name} (${ts.SyntaxKind[declaration.kind]})`)
      }
      if (!targets.length) throw new Error(`导出缺少声明：${file}:${exported.name}`)
      exports.push({ file, name: exported.name, targets: [...new Set(targets)].sort() })
    }
  }
  entries.sort((a, b) => a.id.localeCompare(b.id, 'en'))
  exports.sort((a, b) => (a.file + '#' + a.name).localeCompare(b.file + '#' + b.name, 'en'))
  const entryPoints = []
  if (hasRoot) entryPoints.push({ path: 'mod.ts', sha256: sha(fs.readFileSync(path.join(sdk, 'mod.ts'))) })
  if (fs.existsSync(path.join(sdk, 'package.json'))) {
    entryPoints.push({ path: 'package.json', sha256: sha(fs.readFileSync(path.join(sdk, 'package.json'))), exports: read(path.join(sdk, 'package.json')).exports || {} })
  }
  return { schemaVersion: 1, collectionOnly: true, modules, files: fileRecords, entryPoints, entries, exports }
}

function mappingStatus(fresh, catalog, mapping) {
  if (!isDeepStrictEqual(fresh, catalog)) throw new Error('API 清单与固定源码不一致；不能同时删除清单和映射来缩小分母')
  if (!catalog.entries.length || !catalog.exports.length) throw new Error('API 清单为空')
  if ((mapping.upstreamCommit ?? null) !== (catalog.upstreamCommit ?? null)) throw new Error('API 映射的上游版本不一致')
  const expected = new Set(catalog.entries.map(e => e.id))
  if (!Array.isArray(mapping.entries)) throw new Error('API 映射缺少 entries')
  const actual = new Set()
  for (const entry of mapping.entries) {
    if (actual.has(entry.id)) throw new Error('API 映射 ID 重复：' + entry.id)
    if (!expected.has(entry.id)) throw new Error('API 映射含未知 ID：' + entry.id)
    actual.add(entry.id)
    if (typeof entry.java !== 'string' || !entry.java.startsWith('com.metanet4j.bsv.') || typeof entry.contract !== 'string' || !entry.contract.trim()) throw new Error('API 映射缺少 Java 入口或行为契约：' + entry.id)
  }
  const missing = [...expected].filter(id => !actual.has(id))
  const pending = mapping.entries.filter(e => e.review !== 'reviewed')
  return { missing, pending, actual }
}

function check(fresh, catalog, mapping) {
  const { missing, pending, actual } = mappingStatus(fresh, catalog, mapping)
  if (missing.length || pending.length) throw new Error(`API 未映射 ${missing.length}，未复核 ${pending.length}；不能进入 API 契约验收`)
  console.log(`API 映射结构核对通过：${actual.size} 声明；复核内容、Java 实现与行为等价性仍需独立验收。`)
}

function checkTaskAllocation(catalog, mapping, state, tests) {
  if ((tests.upstreamCommit ?? null) !== (catalog.upstreamCommit ?? null)) throw new Error('任务测试清单的上游版本不符')
  const tasks = state.features.filter(f => f.kind === 'implementation-slice')
  const apiFiles = new Set(catalog.files.map(f => f.path)), testFiles = new Set(tests.files.map(f => f.path))
  const fixtures = new Set(Object.keys(tests.moduleFiles).filter(f => !apiFiles.has(f) && !testFiles.has(f)))
  const apiOwners = new Set(), testOwners = new Set(), fixtureOwners = new Set()
  const reviewed = new Set(mapping.entries.filter(e => e.review === 'reviewed').map(e => e.id))
  function files(task, field, expected, label, owners) {
    if (!Array.isArray(task[field])) throw new Error(`${label}缺少文件清单：${task.id}`)
    const seen = new Set()
    for (const file of task[field]) {
      if (!expected.has(file)) throw new Error(`${label}含未知文件：${file}`)
      if (seen.has(file) || owners?.has(file)) throw new Error(`${label}重复归属：${file}`)
      seen.add(file); owners?.add(file)
    }
  }
  for (const task of tasks) {
    files(task, 'sourceFiles', apiFiles, '实现范围')
    files(task, 'apiCompletionFiles', apiFiles, 'API 收口', apiOwners)
    files(task, 'testFiles', testFiles, '原测试', testOwners)
    files(task, 'regressionTestFiles', testFiles, '累计回归')
    files(task, 'fixtureFiles', fixtures, '辅助资料')
    for (const file of task.fixtureFiles) fixtureOwners.add(file)
    if (task.apiCompletionFiles.some(f => !task.sourceFiles.includes(f))) throw new Error('API 收口文件不在实现范围：' + task.id)
    const refs = state.apiBatches.filter(b => b.apiFiles.some(f => task.sourceFiles.includes(f))).map(b => b.id).sort()
    if (!isDeepStrictEqual(refs, [...(task.apiBatchRefs || [])].sort())) throw new Error('API 复核引用与实现范围不符：' + task.id)
    if (task.status === 'done') {
      if (catalog.entries.some(e => task.apiCompletionFiles.includes(e.file) && !reviewed.has(e.id))) throw new Error('编码任务收口 API 未完成：' + task.id)
      if (!task.evidence?.length) throw new Error('编码任务完成缺少证据：' + task.id)
      const expectedCases = tests.files.filter(f => task.testFiles.includes(f.path)).reduce((n, f) => n + f.cases.length, 0)
      const acceptance = task.taskAcceptance
      const compareReport = acceptance?.compareReport ? path.resolve(__dirname, acceptance.compareReport) : null
      if (!acceptance || acceptance.status !== 'passed' || !acceptance.compareReport
          || !fs.existsSync(compareReport) || acceptance.casesCompared !== expectedCases
          || !(acceptance.assertionsCompared >= 0) || acceptance.missingCases !== 0
          || acceptance.missingAssertions !== 0 || acceptance.uncompared !== 0) {
        throw new Error('编码任务未完成逐断言验收，不能标记 done：' + task.id)
      }
    }
  }
  for (const [expected, actual, label] of [[apiFiles, apiOwners, 'API 收口'], [testFiles, testOwners, '原测试'], [fixtures, fixtureOwners, '辅助资料']]) {
    const missing = [...expected].filter(f => !actual.has(f))
    if (missing.length) throw new Error(`${label}漏文件：${missing.join(', ')}`)
  }
  for (const batch of state.apiBatches) {
    const expected = tasks.filter(t => t.sourceFiles.some(f => batch.apiFiles.includes(f))).map(t => t.id).sort()
    if (!isDeepStrictEqual(expected, [...batch.implementationTasks].sort())) throw new Error('API 复核绑定与编码任务范围不符：' + batch.id)
  }
  console.log(`编码任务 ${tasks.length}：API 文件 ${apiOwners.size}，原测试文件 ${testOwners.size}，原用例 ${tests.files.reduce((n, f) => n + f.cases.length, 0)}，辅助资料 ${fixtureOwners.size}；分配完整不代表实现或测试通过。`)
}

function checkBatches(fresh, catalog, mapping, state, batchId, tests) {
  const all = mappingStatus(fresh, catalog, mapping)
  const records = [...state.features, ...(state.apiBatches || [])]
  const features = new Map()
  for (const feature of records) {
    if (!feature.id || features.has(feature.id)) throw new Error('功能项 ID 重复或缺失：' + feature.id)
    if (!['done', 'in-progress', 'not-started'].includes(feature.status)) throw new Error('功能项状态无效：' + feature.id)
    features.set(feature.id, feature)
  }
  const visited = new Set(), visiting = new Set()
  function visit(feature) {
    if (visiting.has(feature.id)) throw new Error('功能项依赖循环：' + feature.id)
    if (visited.has(feature.id)) return
    visiting.add(feature.id)
    for (const id of feature.dependencies || []) {
      if (!features.has(id)) throw new Error('功能项含未知依赖：' + id)
      visit(features.get(id))
    }
    visiting.delete(feature.id); visited.add(feature.id)
  }
  for (const feature of records) visit(feature)
  const active = state.features.filter(f => f.status === 'in-progress')
  if (state.activeItem != null && !active.some(f => f.id === state.activeItem)) throw new Error('activeItem 未指向进行中事项')
  for (const feature of records) {
    const deps = feature.dependencies || []
    if (feature.status === 'done' && deps.some(id => features.get(id).status !== 'done')) {
      throw new Error('前置事项未完成：' + feature.id)
    }
    if (feature.status === 'in-progress' && deps.some(id => features.get(id).status === 'not-started')) {
      throw new Error('前置事项未完成：' + feature.id)
    }
  }
  if (state.nextItem != null && !features.has(state.nextItem)) throw new Error('nextItem 指向未知事项')
  if (state.apiBatches && state.nextItem != null && !state.features.some(f => f.id === state.nextItem)) throw new Error('nextItem 必须指向执行事项，API 复核嵌入编码任务')
  const batches = state.apiBatches || state.features.filter(f => f.kind === 'api-batch')
  if (!batches.length) throw new Error('API 批次为空')
  const gate = features.get('migration-api-contract')
  if (!gate || gate.kind !== 'gate' || batches.some(b => !gate.dependencies?.includes(b.id))) throw new Error('API 总验收未依赖全部批次')
  const expectedFiles = new Set(catalog.files.map(f => f.path)), assigned = new Set()
  const mapped = new Map(mapping.entries.map(e => [e.id, e]))
  const rows = batches.map(batch => {
    if (state.apiBatches && (!batch.implementationTasks?.length || batch.implementationTasks.some(id => !state.features.some(f => f.id === id && f.kind === 'implementation-slice')))) throw new Error('API 复核未绑定有效编码任务：' + batch.id)
    if (batch.parentId !== gate.id) throw new Error('API 批次父项无效：' + batch.id)
    if (!Array.isArray(batch.apiFiles) || !batch.apiFiles.length) throw new Error('批次缺少完整文件：' + batch.id)
    for (const file of batch.apiFiles) {
      if (!expectedFiles.has(file)) throw new Error('批次含未知文件：' + file)
      if (file.split('/')[1] !== batch.module) throw new Error('批次文件模块不符：' + file)
      if (assigned.has(file)) throw new Error('批次文件重复归属：' + file)
      assigned.add(file)
    }
    const entries = catalog.entries.filter(e => batch.apiFiles.includes(e.file))
    return { batch, total: entries.length, missing: entries.filter(e => !mapped.has(e.id)).length,
      pending: entries.filter(e => mapped.has(e.id) && mapped.get(e.id).review !== 'reviewed').length }
  })
  const missingFiles = [...expectedFiles].filter(file => !assigned.has(file))
  if (missingFiles.length) throw new Error('API 批次漏文件：' + missingFiles.join(', '))
  for (const row of rows) {
    if (row.batch.status === 'done' && (row.missing || row.pending)) throw new Error('未完成批次不能标记 done：' + row.batch.id)
    if (row.batch.status === 'done' && (!Array.isArray(row.batch.evidence) || !row.batch.evidence.length)) throw new Error('完成批次缺少证据：' + row.batch.id)
  }
  if (tests) checkTaskAllocation(catalog, mapping, state, tests)
  if (batchId) {
    const row = rows.find(r => r.batch.id === batchId)
    if (!row) throw new Error('未知 API 批次：' + batchId)
    if (row.missing || row.pending) throw new Error(`批次 ${batchId} 未映射 ${row.missing}，未复核 ${row.pending}`)
    console.log(`单批设计映射结构通过：${batchId}，${row.total} 声明；不是完整 API 或 SDK 验收。`)
  } else {
    console.log(`分批覆盖核对：${assigned.size} 文件，${catalog.entries.length} 声明，${batches.length} 批次；未映射 ${all.missing.length}，未复核 ${all.pending.length}。`)
    for (const row of rows) console.log(`${row.batch.id} [${row.batch.status}]：${row.batch.apiFiles.length} 文件，${row.total} 声明，已复核 ${row.total - row.missing - row.pending}，未映射 ${row.missing}，未复核 ${row.pending}`)
    console.log('以上仅核对分批覆盖和进度；不是完整 API 或 SDK 验收。')
  }
}

if (require.main === module) {
  try {
    const args = process.argv.slice(2), command = args.shift(), options = { modules: [] }
    while (args.length) {
      const key = args.shift(), value = args.shift()
      if (!value || !['--sdk', '--module', '--output', '--catalog', '--mapping', '--features', '--batch'].includes(key)) throw new Error('未知或缺失参数：' + key)
      if (key === '--module') options.modules.push(value)
      else options[key.slice(2)] = value
    }
    if (!['inventory', 'check', 'batches'].includes(command) || (command === 'inventory' && !options.output)) throw new Error('用法：node audit-api.cjs inventory --output PATH；check；batches [--batch ID]')
    if ((options.batch || options.features) && command !== 'batches') throw new Error('--batch/--features 仅用于 batches，不能缩小正式 check 范围')
    const scope = read(path.join(__dirname, 'module-scope.json'))
    const modules = options.modules.length ? options.modules : scope.selectedModules
    if (!modules?.length || modules.some(m => !/^[a-z][a-z0-9-]*$/.test(m)) || new Set(modules).size !== modules.length) throw new Error('必须指定不重复的完整模块名')
    const sdk = path.resolve(options.sdk || realSdk)
    if (sdk === realSdk) {
      if (execFileSync('git', ['-C', sdk, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim() !== scope.upstreamCommit || execFileSync('git', ['-C', sdk, 'status', '--porcelain', '--untracked-files=all'], { encoding: 'utf8' }).trim()) throw new Error('固定 TS 上游提交或工作树不符')
      if (!isDeepStrictEqual(modules, scope.selectedModules)) throw new Error('正式 API 清点必须覆盖全部选定模块')
    }
    const data = inventory(sdk, modules)
    if (sdk === realSdk) data.upstreamCommit = scope.upstreamCommit
    if (command === 'inventory') {
      fs.writeFileSync(options.output, JSON.stringify(data, null, 2) + '\n')
      console.log(`API 清点：${data.files.length} 文件、${data.entries.length} 声明、${data.exports.length} 导出；未执行源码或验证行为。`)
    } else {
      const catalog = read(options.catalog || path.join(__dirname, 'api-catalog.json')), mapping = read(options.mapping || path.join(__dirname, 'api-map.json'))
      if (command === 'batches') {
        const featureFile = options.features || path.join(__dirname, 'feature_list.json'), state = read(featureFile)
        const testRef = state.implementationPolicy?.testCatalogRef
        const tests = testRef ? read(path.resolve(path.dirname(featureFile), testRef)) : undefined
        checkBatches(data, catalog, mapping, state, options.batch, tests)
      }
      else check(data, catalog, mapping)
    }
  } catch (error) { console.error(error.message); process.exitCode = 1 }
}
