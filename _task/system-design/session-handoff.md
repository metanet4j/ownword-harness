# 当前交接：v0.2.0 设计待审核

事项 `frontend-content-v020-integration-design` 的认知、实现设计和只读取证已交付，状态 needs-review，implementationAuthorized=false。入口为[实现设计](spec/frontend/设计文档v0.2.0-内容真实集成-20261014-215514.md)与[检查证据](evidence/v020-design-20261014-215514/verification.json)。

唯一下一步是用户审核文档并裁决设计第 5 节 R01。用户原话“通过后开始实现”仍有效；本次“继续”用于完成待交付设计，不推定为对尚未提交方案的批准。若批准方案 B，先将获准的限定扩展更新到总认知和实现设计，再按第 9 节开工；若选 A，需补齐现成 Revision 契约证据并重新审核阻塞部分。

不要提前创建实现 worktree、升级依赖或发送交易。实际基线为原型 fb6ed59、前端 04bb127、后端组件 11f925f；开工前复核是否变化。原型包括后续版本，只迁移本期 C01–C10 相关页面。高层 BSocial 模板 MIME/app 输出问题已有可复跑实验；不能直接用会自动广播的 Action 绕过准备与持久化。

v0.1 未关闭的公共历史/checkpoint、真实扩展、主网和视觉人工复核门禁见其统一任务清单。根仓库已有与本任务无关的 AGENTS、infra、skills-lock、nljk 删除等改动，继续保留。无需启动或停止已有 v0.1 服务。
