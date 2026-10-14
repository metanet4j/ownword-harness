# 当前交接

F06 最新原型 UI 还原已提交 7e9d9ab，原型来源 fb6ed59；v0.1 适用页面布局、双语主题和响应式对照通过。六组共同测量区域无超过 0.1px 差异；真实模拟文案及范围差异单独记录。lint、typecheck、29 项测试、build、实际创建／取消重试／后端回读／复制／键盘翻面通过，9 份 axe 无 violation。视觉成果 needs-review 供用户复核，activeItem=null。

最新对照：[截图与验收](evidence/ui-latest-20261014/index.html)，运行入口 http://127.0.0.1:5050；实际应用 http://127.0.0.1:5041。完整限制、字体网络日志和复跑命令见[当前报告](验收报告v0.1.0-20261014-010853.md)。未做读屏软件测试，主网和公共索引门禁保留。

5041 production、5048 官方核心钱包、5043 API 已恢复 ready。当前已关闭旧前端 ChunkLoadError 资源引用问题，F05 代码 bde801a 保留。后端 11f925f 本轮未改；旧 5042 钱包及未知操作保留。构建前须先停止前端，不能运行中覆盖 .next。私有运行配置和钱包存储在忽略的 _runtime，未清空共享数据或推送。

本轮 UI 新建身份使用独立钱包，BAP ID iXAtyKjETfjAZgbVr4nfski32Bm，资料 UI acceptance updated，详见后端证据；不修改主账户 0 Maya Chen 1 与账户 1 RPC session verification。允许范围为官方核心真实签名、独立 Mock 广播及真实 Java/MongoDB 读写，scope=broadcast-mock 不代表主网事实。

当前 UI 交付的下一步为用户视觉复核。整体产品后续仍需核实 Chrome 扩展准备不广播能力、充分公共历史与 checkpoint，充值后执行 I08/I09；本轮不关闭 B06/B07/B08 或主网门禁。

复跑 `./init.sh`；前端命令及测试环境见 README 与验收汇总。最终浏览器会话 ui-final 保留主账户身份页；ui-smoke 为新的欢迎页加载检查。原型未改，旧 tag 不移动；新的 UI commit/tree 单独登记在 feature_list.environment。所有 after 截图为 production，同视口对照 JSON 容差 0.1px，未声称逐像素完全相同。

稳定 WalletProvider 契约与官方核心模块未改。私有助记词、SQLite、旧未知交易不能删除或盲目重签；UI 新测试钱包保留在 _runtime/ui-wallet，可按其私有配置恢复。保留已有设计文档 needs-review 状态，无需重新申请已明确授权范围的工作许可。

本轮临时 5049 dev、5051 测试钱包、5052 测试前端已停止，持久数据保留。5050 为对照报告静态服务；重开可运行 `python3 -m http.server 5050 --bind 127.0.0.1 --directory evidence/ui-latest-20261014`。
