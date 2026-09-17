# 当前交接

## 当前目标（Current Objective）

v0.2.0 文字内容高保真原型。H00 文档、worktree 与 harness 已交付待复核；C01–C10 尚未开始。签名与上链属于必备交互，但使用可控样例，不接真实服务。

## 文件（Files）

先读 `AGENTS.md`、`feature_list.json` 和 `progress.md`，再读当前功能对应 PRD。基线、分支、版本和来源路径登记在功能清单；功能事实只在 PRD 和核心认知中维护。

`ownword-prototype/` 是后续制作目录，基线为原型 dev 的已提交成果。外围文档与 harness 在根仓库管理，源代码不纳入根仓库。

## 当前验证与运行环境

`./init.sh` 已在宿主运行，92 条既有模型断言通过，harness 结构评分 100/100。桌面和 320px 的基线页面、模拟连接取消验证通过，三张截图已查看，浏览器运行错误为空；证据路径见 progress。原型代码未修改，不能把上述结果当成内容功能验收。

新预览 `http://127.0.0.1:4312/` 已运行；旧版 4311 保留。访问日志 `.runtime/preview.log`，完整启动日志 `.runtime/bootstrap-serve.log`。重启时先检查端口；仅停止自己启动的进程，不处理其他服务。标准启动命令为 `./init.sh --serve`，环境可重复启动（restartable）。

## 阻塞（Blockers）

无已知阻塞。H00 和 v0.1 视觉成果仍待用户复核，不自动标记 done。根仓库原有技能文件删除与新增保留，不纳入本任务提交。

## 唯一下一步（Recommended Next Step）

后续从 C01 内容入口与工作台开始：运行 `./init.sh`，将 C01 设为唯一 `in-progress`，按 PRD 第 4.1、4.2 节制作并验证 C01-A/B。本轮请求到文档与环境初始化为止，不提前实现内容页面。
