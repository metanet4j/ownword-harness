# 当前进展

## 当前状态（Current State）

C01–C10、R01–R03 均已实现、定向验证并提交，状态 needs-review，等待用户复核。无进行中功能。

## 验证证据（Verification Evidence）

当前交付为可视化 Markdown 编辑：默认排版正文编辑，可切换源码、双栏和预览；格式、链接校验、任务勾选、撤销及中文连续输入通过。仅切换模式、语言或主题不改写原文；含 BOM/CRLF 的实际导入导出逐字节比对通过。自动保存、刷新恢复与立即检查发布使用最新正文。

桌面浅深色和 390/320px 截图已审阅；手机切换保持编辑位置，页面无横向溢出。浏览器无运行错误，./init.sh 通过。提交与证据以 feature_list.json 和 ownword-prototype/evidence/R03/verification.json 为准。

## 文件与运行（Files）

原型 ownword-prototype/，分支 prototype/v0.2.0-content。预览 http://127.0.0.1:4312/#/content；./init.sh 检查，./init.sh --serve 启动，日志 .runtime/preview.log。旧版 4311 保留；签名、发布与 Proof 仍为模拟。

## 下一步与限制（Next）

用户刷新后打开或新建草稿，复核可视化编辑。可视化实际编辑会规范化 Markdown 标记；特殊语法保留全文并提供源码入口。未执行系统输入法组合、Safari、实体手机或全量旧版回归。

v0.2.0 分支尚未合并或推送；测试浏览器已关闭，预览服务保留。根仓库原有技能改动保留。
