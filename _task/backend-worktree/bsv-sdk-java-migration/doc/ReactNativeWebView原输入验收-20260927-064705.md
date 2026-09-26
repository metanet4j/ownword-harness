# ReactNativeWebView 原输入局部验收

固定上游提交为 `f999e0c1aad9a7afd0cbadaaf23841d049af9d5a`，原文件为 `src/wallet/substrates/__tests/ReactNativeWebView.test.ts`。本次覆盖全文件 25 例及实际执行的 40 条原断言。[局部计划](../.cache/evidence/react-native-plan-20260927/)由固定 Jest 运行时采集的 88 条入口冻结：构造 25、公开 `invoke` 21、原生桥发帧 20、消息派发 22。

[固定 Jest](../.cache/evidence/react-native-ts-formal-v2-20260927/)运行 25/25，[主 Java 提交 `46210f5` 的 Surefire](../.cache/evidence/react-native-java-formal-20260927/)运行 25/25，均无失败、错误或跳过。[双侧打包结果](../.cache/evidence/react-native-parity-20260927.json)逐项确认 88/88 个真实输入及 40/40 条原断言实际值相同；`audit-tests.py compare` 返回 `PASS`、25 例、40 条断言。它是单文件局部结果，`formalAcceptance=false`；完整模块与 5329 例最终验收由统一采集完成。

Java 的零、一、二参构造对应原测试实际调用；宿主的 `nativeRequestId()` 默认仍使用 `Random.random(12)` 和 `Utils.toBase64`，测试宿主提供固定 Jest 的 `request-id`。原生桥发出的完整 JSON 字符串、消息来源、origin 和派发数据均在入口核对。隔离复验见 [25/25、88/88、40/40 轨迹](../.cache/evidence/react-native-java-isolated-v2-20260927/)。输入探针保留原监听器函数名；[无输入探针的原断言轨迹](../.cache/evidence/react-native-ts-assertion-baseline-20260927/assertions.raw.jsonl)与正式 TS 原断言原始轨迹 SHA-256 相同，均为 `b45679231913e7bac85cccb0ec86aa0d53bd25b14e39cd03cdac78f2f12b5ea7`。

把一条 Java 公开调用的 `getVersion` 改一个字符，或把首条原断言的错误消息末尾改一个字符，标准打包器均退出 2，分别报出[同输入差异](../.cache/evidence/react-native-tamper-input-20260927.log)和[实际结果差异](../.cache/evidence/react-native-tamper-assertion-20260927.log)。重跑入口为 `capture-react-native-side.py`；固定 TS 测试源码未改动。
