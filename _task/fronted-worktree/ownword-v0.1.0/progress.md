# 当前状态

F06 最新原型 UI 还原已提交 7e9d9ab，原型来源 fb6ed59；v0.1 适用页面布局、双语主题和响应式对照通过。六组共同测量区域无超过 0.1px 差异；真实模拟文案及范围差异单独记录。lint、typecheck、29 项测试、build、实际创建／取消重试／后端回读／复制／键盘翻面通过，9 份 axe 无 violation。视觉成果 needs-review 供用户复核，activeItem=null。

最新对照：[截图与验收](evidence/ui-latest-20261014/index.html)，运行入口 http://127.0.0.1:5050；实际应用 http://127.0.0.1:5041。完整限制、字体网络日志和复跑命令见[当前报告](验收报告v0.1.0-20261014-010853.md)。未做读屏软件测试，主网和公共索引门禁保留。

5041 production、5048 官方核心钱包、5043 API 已恢复 ready。当前已关闭旧前端 ChunkLoadError 资源引用问题，F05 代码 bde801a 保留。后端 11f925f 本轮未改；旧 5042 钱包及未知操作保留。构建前须先停止前端，不能运行中覆盖 .next。私有运行配置和钱包存储在忽略的 _runtime，未清空共享数据或推送。

本轮 UI 新建身份使用独立钱包，BAP ID iXAtyKjETfjAZgbVr4nfski32Bm，资料 UI acceptance updated，详见后端证据；不修改主账户 0 Maya Chen 1 与账户 1 RPC session verification。允许范围为官方核心真实签名、独立 Mock 广播及真实 Java/MongoDB 读写，scope=broadcast-mock 不代表主网事实。

当前 UI 交付的下一步为用户视觉复核。整体产品后续仍需核实 Chrome 扩展准备不广播能力、充分公共历史与 checkpoint，充值后执行 I08/I09；本轮不关闭 B06/B07/B08 或主网门禁。
