# Git 提交规范

## 1. 适用范围

- 适用于 `harness-hh` 下所有需要 `git add`、`git commit`、`git push` 的场景。

## 2. 提交格式

默认遵循 [Conventional Commits 1.0.0（中文）](https://www.conventionalcommits.org/zh-hans/v1.0.0/)：

```text
<type>[optional scope][!]: <description>
```

## 3. 强制规则

- `type` 必填。
- `scope` 可选，使用圆括号包裹。
- `:` 后必须保留一个空格。
- 新功能必须使用 `feat`。
- 缺陷修复必须使用 `fix`。
- 破坏性变更必须通过以下任一方式标记：
  - 在标题中使用 `!`，例如 `feat(api)!: ...`
  - 在脚注中使用 `BREAKING CHANGE: <description>`
- 可选正文和标题之间必须空一行。
- 可选脚注和正文之间必须空一行。
- 脚注使用 trailer 风格，例如 `Refs: #123`。

## 4. 常用类型

- `feat`
  - 新功能。

- `fix`
  - 缺陷修复。

- `docs`
  - 文档调整。

- `refactor`
  - 不改变外部行为的重构。

- `perf`
  - 性能优化。

- `test`
  - 测试补充或调整。

- `build`
  - 构建系统或依赖调整。

- `ci`
  - CI 配置调整。

- `chore`
  - 杂项维护。

- `style`
  - 不影响行为的格式调整。

- `revert`
  - 回滚提交。

## 5. 语义版本映射

- `fix` 对应 `PATCH`。
- `feat` 对应 `MINOR`。
- 含破坏性变更对应 `MAJOR`。

## 6. 提交前校验

- 先执行 `git status --short`，确认工作区范围。
- 先执行 `git diff --name-only --cached`，确认暂存范围。
- 只提交当前任务相关文件，不混入无关改动。
- 提交信息应直接说明这次改了什么，不写空泛描述。

## 7. 示例

```text
docs(standards): 新增仓库级规范目录
feat(login): 支持微信扫码登录
fix(udb): 修正手机号历史判定条件
```
## 8.使用中文
- 提交内容请使用中文描述
feat(login): 支持微信扫码登录

## 多子仓库 
- 任务涉及到多子仓库，分支命名统一