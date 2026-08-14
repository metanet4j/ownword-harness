# 交接

## 当前事项

四风格原型对比，各为独立仓库：

| 仓库 | 风格 | 状态 |
| --- | --- | --- |
| `designs/own-word-prototype-006` | 碑刻与航图（纪念碑居中布局） | in-progress（activeItem design-001），资产 needs-review |
| `designs/own-word-prototype-006-2` | 灯塔与信号（信号控制台布局） | blocked（design-002，保留为对比候选），资产 needs-review |
| `designs/own-word-prototype-006-3` | 地平线与大陆（航海日志布局） | blocked（design-003，保留为对比候选），资产 needs-review |
| `designs/own-word-prototype-006-4` | 地平与穹顶（天文观测台布局：穹顶天幕+基准线+游标读数+姓名星座化） | blocked（design-004，保留为对比候选），资产 needs-review |

四套功能一致，布局/结构/交互各自独立。验证脚本 CDP 端口：006-2 用 9222/9224，006-3 用 9232/9234，006-4 用 9242/9244，不可并行重复端口。

预览（服务：`python -m http.server 4311 --directory C:\haodev\ownword\designs`）：

- `http://127.0.0.1:4311/own-word-prototype-006/index.html`
- `http://127.0.0.1:4311/own-word-prototype-006-2/index.html`
- `http://127.0.0.1:4311/own-word-prototype-006-3/index.html`
- `http://127.0.0.1:4311/own-word-prototype-006-4/index.html`

## 唯一下一步

等待用户四套对比复核并选定风格。选定后：

1. 选定仓库资产 `record-asset.mjs --status approved`；其余三套按用户意见保留或删除。
2. 功能迭代只落在选定仓库，重跑其 `_verify.mjs` 与 `_audit.mjs`，Git 提交带 `(PRD v0.1)`。
3. 对应 feature 项标记 done（evidence 补人工复核记录），根仓库 commit。
4. 处理 `progress.md`「对 PRD / 后端设计的同步事项」中用户认可的条目。
