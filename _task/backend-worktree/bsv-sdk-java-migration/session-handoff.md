# 会话交接

## 当前状态

本轮修复与正式全量验收已完成。43 个事项全部 `done`，下一项为空；当前证据与完整覆盖见 [progress.md](progress.md)。

正式来源：`.cache/evidence/full-run-repaired-20261012/full-run.json`，`status=passed`、`formalAcceptance=true`，133 原文件、5329 原用例、38092 输入、56744 实际断言；四阶段均 exit=0，耗时 5072.2 秒。

输入缺口及输入替换均为 0。32 条原样不可达站点按用户确认保留证明，另有独立有效 DRBG 分支 3/3 通过，不计入原例。

## 只读复核

在 `/home/haodev/ownword/_task/backend-worktree/bsv-sdk-java-migration` 执行：

```bash
RUN_FOLDER=.cache/evidence/full-run-repaired-20261012
python3 full-evidence-run.py verify "$RUN_FOLDER/full-run.json"
python3 audit-tests.py check --catalog module-tests.json --mapping test-map.json \
  --input-plan "$RUN_FOLDER/input-plan.json" --ts-inputs "$RUN_FOLDER/ts-inputs.jsonl" \
  --java-inputs "$RUN_FOLDER/java-inputs.jsonl" --ts-assertions "$RUN_FOLDER/ts-assertions.jsonl" \
  --java-assertions "$RUN_FOLDER/java-assertions.jsonl" --ts-run-manifest "$RUN_FOLDER/ts-run.json" \
  --java-run-manifest "$RUN_FOLDER/java-run.json" --ts-report "$RUN_FOLDER/ts-jest.json" \
  --java-report "$RUN_FOLDER/java-surefire.xml" --observations "$RUN_FOLDER/parity-results.json"
node audit-api.cjs check
```

三个入口已独立复跑 exit=0，日志在 `.cache/evidence/repair-exceptions-20261012/final-*.log`。Node/git 子进程及完整运行在本机需宿主权限；Maven/pnpm 必须使用任务入口。

## 已验证交付

当前 Java 完整 `clean test` 5451/5451，失败/错误/跳过为 0。SDK 和 sources JAR 已安装 `.cache/maven/com/metanet4j/metanet4j-bsv-sdk/0.2.0/`；字节码 major 69、六模块和许可资源齐全，详见 `.cache/evidence/repair-exceptions-20261012/delivery.json`。

SDK HEAD `6a5569a`，工作树干净；Java 来源摘要 `f12d567a889626d019ef9404b0650a1a11c7f70d22e88a118e6d30bc4fbbc6a0`，完整运行 ID `1958913b59f84b43a4712a4ae07c7bc1`。固定 TS 上游 `f999e0c1aad9a7afd0cbadaaf23841d049af9d5a`，全程只读；其他四工程未引入修改。

## 后续约束

SDK、根 `.py/.cjs/.mjs/.sh`、清单、映射、输入计划或豁免登记的变化会使本轮证据不能直接沿用；重新采集必须使用新目录，默认 90 分钟，只有真实同源超时来源才允许 180 分钟重试。

普通测试和广播/钱包场景保持离线，不调用真实资金或业务接口；只在 `metanet4j-bsv-sdk` 内继续开发。本轮没有待处理的实施事项。SDK 的 `origin` 为 `https://github.com/metanet4j/metanet4j-bsv-sdk.git`，迁移分支已推送并设置 upstream，远端 HEAD 已核对为 `6a5569a72c33463e1a48bd405b8f7b564583ad11`。任务根仓库文档和工具已本地提交，推送范围待用户确认。
