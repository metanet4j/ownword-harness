// 使用固定上游自己的 Jest 注册测试，清点时不执行测试体和 hooks。
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const crypto = require('node:crypto')
const { createRequire } = require('node:module')
const { spawnSync } = require('node:child_process')
const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'workspace.json')))
const realSdk = path.resolve(__dirname, '../../..', config.upstream.path, config.upstream.packagePath)
const upstreamRequire = createRequire(path.join(realSdk, 'package.json'))
const sha = value => crypto.createHash('sha256').update(value).digest('hex')

class CensusEnvironment extends upstreamRequire('jest-environment-node').TestEnvironment {
  constructor(options, context) {
    super(options, context)
    this.testPath = context.testPath
  }

  handleTestEvent(event, state) {
    if (event.name !== 'run_start') return
    const file = path.relative(process.env.MIGRATION_CENSUS_SDK, this.testPath).split(path.sep).join('/')
    const cases = []
    const occurrences = new Map()
    function walk(block, names, inheritedMode) {
      // 清点专用进程不应运行 before/after hooks。
      block.hooks = []
      for (const item of block.children) {
        const mode = inheritedMode === 'skip' ? 'skip' : (item.mode || inheritedMode || 'run')
        if (item.type === 'describeBlock') walk(item, [...names, item.name], mode)
        else {
          const fullNames = [...names, item.name]
          const key = JSON.stringify(fullNames)
          const occurrence = (occurrences.get(key) || 0) + 1
          occurrences.set(key, occurrence)
          cases.push({ id: sha(JSON.stringify([file, fullNames, occurrence])), names: fullNames, occurrence, mode })
          item.mode = 'skip'
        }
      }
    }
    walk(state.rootDescribeBlock, [], null)
    fs.writeFileSync(path.join(process.env.MIGRATION_CENSUS_DIR, sha(file) + '.json'), JSON.stringify({ path: file, cases }))
  }
}
module.exports = CensusEnvironment

function staticSites(file, text) {
  const ts = upstreamRequire('typescript')
  const source = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true)
  const sites = []
  function root(expression) {
    while (ts.isCallExpression(expression) || ts.isPropertyAccessExpression(expression) || ts.isTaggedTemplateExpression(expression)) {
      expression = ts.isTaggedTemplateExpression(expression) ? expression.tag : expression.expression
    }
    return ts.isIdentifier(expression) ? expression.text : ''
  }
  function visit(node) {
    let kind
    if (ts.isCallExpression(node)) {
      const name = root(node.expression)
      if (name === 'expect' && ts.isIdentifier(node.expression)) kind = 'assertion'
      if (['it', 'test', 'fit', 'xit'].includes(name) && !(ts.isPropertyAccessExpression(node.expression) && node.expression.name.text === 'each')) kind = 'registration'
    }
    if (ts.isForStatement(node) || ts.isForOfStatement(node) || ts.isForInStatement(node) || ts.isWhileStatement(node) || ts.isDoStatement(node)) kind = 'loop'
    if (ts.isIfStatement(node) || ts.isConditionalExpression(node)) kind = 'conditional'
    if (kind) {
      const position = source.getLineAndCharacterOfPosition(node.getStart(source))
      const line = position.line + 1
      const column = position.character + 1
      sites.push({ id: `${file}:${line}:${column}:${kind}`, kind, line, column })
    }
    ts.forEachChild(node, visit)
  }
  visit(source)
  return sites
}

function moduleDependencies(sdk, files) {
  const ts = upstreamRequire('typescript')
  const graph = {}
  for (const module of [...new Set(files.map(f => f.split('/')[1]))].sort()) {
    const dependencies = new Set()
    const folder = path.join(sdk, 'src', module)
    for (const relative of fs.readdirSync(folder, { recursive: true })) {
      if (!relative.endsWith('.ts') || relative.endsWith('.d.ts') || relative.endsWith('.test.ts') || relative.split(path.sep).some(p => p.startsWith('__'))) continue
      const file = path.join(folder, relative)
      const emitted = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText
      const ast = ts.createSourceFile(file, emitted, ts.ScriptTarget.Latest, true)
      for (const node of ast.statements) {
        if (!(ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) || !node.moduleSpecifier?.text?.startsWith('.')) continue
        const target = path.relative(path.join(sdk, 'src'), path.resolve(path.dirname(file), node.moduleSpecifier.text)).split(path.sep)[0]
        if (target !== module && !target.startsWith('..')) dependencies.add(target)
      }
    }
    graph[module] = [...dependencies].sort()
  }
  return graph
}

if (require.main === module) {
  let temporary
  try {
    const args = process.argv.slice(2)
    const sdk = path.resolve(args.splice(args.indexOf('--sdk'), 2)[1])
    const output = path.resolve(args.splice(args.indexOf('--output'), 2)[1])
    if (!args.length || args.some(file => file.startsWith('-') || !fs.statSync(path.join(sdk, file)).isFile())) throw new Error('必须提供明确的测试文件清单')
    temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'bsv-census-'))
    const result = spawnSync(process.execPath, [upstreamRequire.resolve('jest/bin/jest'), '--runInBand', '--watchman=false', '--runTestsByPath', ...args,
      '--testEnvironment', __filename, '--testPathIgnorePatterns', '/node_modules/', '--json', '--outputFile', path.join(temporary, 'jest.json')], {
      cwd: sdk, encoding: 'utf8', maxBuffer: 32 * 1024 * 1024,
      env: { ...process.env, MIGRATION_CENSUS_DIR: temporary, MIGRATION_CENSUS_SDK: sdk }
    })
    if (result.status !== 0) throw new Error(result.stdout + result.stderr)
    const files = args.sort().map(file => {
      const collected = JSON.parse(fs.readFileSync(path.join(temporary, sha(file) + '.json')))
      if (!collected.cases.length) throw new Error('未注册任何用例：' + file)
      const raw = fs.readFileSync(path.join(sdk, file))
      return { ...collected, sha256: sha(raw), sites: staticSites(file, raw.toString('utf8')) }
    })
    fs.writeFileSync(output, JSON.stringify({ collectionOnly: true, moduleDependencies: moduleDependencies(sdk, args), files }, null, 2) + '\n')
    console.log(`清点 ${files.length} 文件、${files.reduce((n, f) => n + f.cases.length, 0)} 用例；未执行测试体。`)
  } catch (error) {
    console.error(error.message)
    process.exitCode = 1
  } finally {
    if (temporary) fs.rmSync(temporary, { recursive: true, force: true })
  }
}
