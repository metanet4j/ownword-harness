---
name: prototype-versioning
description: 在提交原型改动、递增或标记原型版本、更新 version.json 与构建清单，或按原型版本对齐实现时使用。定义 PRD 版本、原型增量版本、内容版本和 Git trailers 的机器可读格式。
---

# 原型版本与提交

## 两个轴

- 载体版本：`v<载体 PRD 版本>-r<N>`，被修改的原型与增量序号，例如 `v0.4.0-r3`。
- 内容版本：改动服务的页面/功能由哪份 PRD 定义，例如 `v0.2.0`。

两者可以不同。在 v0.4.0 原型上改“我的内容”列表，载体是 v0.4.0，内容是 v0.2.0。载体不能代替内容版本。

## 判定内容版本

按页面和功能查 PRD，不能按 worktree、分支、`baseVersion` 或载体版本推断。

1. 定位改动的页面与功能编号，例如“我的内容”C01、“草稿管理”C04。
2. 在 `_task/system-design/spec/prd/<版本>/设计文档*.md` 中找定义该页面、结构或流程的版本。
3. 后续版本 PRD 只写“由原模块承接”“复用原实现”“不覆盖旧模块”时，内容版本归最初定义该模块的版本。
4. 页面跨版本演化、依据不足时，列出候选并向用户确认，不猜。

| 页面/模块 | 内容版本 | 依据 |
| --- | --- | --- |
| 连接、身份设置、身份资料 | v0.1 | `prd/v0.1/设计文档v0.1.md` |
| 我的内容、草稿列表、编辑、发布、阅读、修订 | v0.2.0 | `prd/v0.2.0/设计文档v0.2.0-20260917-210556.md`（C01、C04、C07） |
| Artifact、数字 ID、转移、查找、公开身份 | v0.3.0 | `prd/v0.3.0/设计文档v0.3.0-20260918-215142.md` |
| 个人主页、公开主页、关系 | v0.4.0 | `prd/v0.4.0/设计文档v0.4.0-个人主页-20260918.md` |
| 首页叙事与公开探索 | v0.3.0 | 由提交 be03af4 引入，v0.4.0 PRD 未定义该页 |

## 编号规则

`rN` 按载体独立计数，不从内容版本继承：

- 一次向用户交付（实现、验证、提交）加一。
- 同一交付内的修正提交沿用该版本。
- 载体基础版本升级时重置，例如 v0.5.0 的首个交付是 `v0.5.0-r1`。
- 同一内容在多个载体落地时，各自按载体计数，版本号不共用。

## 记录位置

全部位于原型仓库，根仓库不跟踪任务子目录。

| 位置 | 内容 | 作用 |
| --- | --- | --- |
| `version.json` | 当前版本状态 | 唯一事实源，脚本直接读取 |
| `package.json` `version` | `0.4.0-r3` | npm/semver 可读，必须与 version.json 一致 |
| `vendor/build-manifest.json` `version` | 构建时的版本对象 | 构建产物自证，`--check` 校验 |
| 提交 trailer | `Prototype-Version`、`Content-Version`、`PRD-Version`、`Timestamp` | 每条提交自描述，可检索历史 |

Git tag 不自动创建。用户明确要求打 tag 时，才以 `Prototype-Version` 同名创建，并指向该交付提交。

```json
{
  "schemaVersion": 2,
  "prototypeVersion": "v0.4.0-r3",
  "carrier": {
    "version": "v0.4.0",
    "baseline": "5b3cdf8",
    "branch": "codex/prototype-official-s2"
  },
  "content": [
    {
      "version": "v0.2.0",
      "doc": "v0.2.0_20260917-210556"
    }
  ]
}
```

`content` 为数组，一次改动涉及多版内容时逐项列出；`doc` 取设计文档文件名中的版本与时间戳。

## 提交格式

标题以载体版本开头，正文写范围与验证，末尾用 Git trailers：

```
v0.4.0-r3 内容列表行右侧布局收拢

范围：草稿与已发布列表行、⋯ 菜单位置、右列状态与日期合并
验证：build/check 通过；1440/390、中英深浅色

Prototype-Version: v0.4.0-r3
Content-Version: v0.2.0
PRD-Version: v0.2.0_20260917-210556
Timestamp: 2026-10-21 14:29:06
```

trailer 键固定为 `Prototype-Version`、`Content-Version`、`PRD-Version`、`Timestamp`。`Timestamp` 为交付时本地时间，格式 `yyyy-MM-dd HH:mm:ss`，修正提交信息时不改写交付时间。

## 跨版本内容

载体与内容不同时，`Prototype-Version` 用载体序号，`Content-Version` 写内容版本，`PRD-Version` 写该内容文档的版本与时间戳。

同一结论在内容版本的原生分支落地时，单独提交对应版本，两个提交正文互引；不把同一个 tag 挂到两处。

## 读取与增量

```bash
node -p "require('./version.json').prototypeVersion"
node -p "require('./version.json').content[0].version"
node -p "require('./vendor/build-manifest.json').version.prototypeVersion"
git log --format='%h %(trailers:key=Prototype-Version,valueonly) %(trailers:key=Content-Version,valueonly) %(trailers:key=Timestamp,valueonly)'
git log --all --format='%h %(trailers:key=Content-Version,valueonly)' | grep v0.2.0
git diff <旧版本提交>..<新版本提交> --stat
```

实现方按 `Prototype-Version` 对齐原型版本；需要某版内容的全部改动时，按 `Content-Version` 检索。未打 tag 时用提交号做区间对比，版本号仍可从 trailer 读出。

## 检查清单

- [ ] 内容版本按页面/功能查 PRD 得出，未用载体版本或分支名代替
- [ ] `version.json`、`package.json`、`build-manifest.json` 三处版本一致
- [ ] 提交标题以 `Prototype-Version` 开头，正文含四个 trailer
- [ ] `Content-Version` 与 `PRD-Version` 指向同一份设计文档
- [ ] `Timestamp` 为交付时本地时间，格式 `yyyy-MM-dd HH:mm:ss`
- [ ] 未自动创建 tag；用户要求时才创建与 `Prototype-Version` 同名的 tag
- [ ] 版本变更后重新构建，`build-prototype --check` 通过
