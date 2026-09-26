# progress.md — Boot 4 / Java 25 测试任务

范围与验收标准见[单元测试全覆盖计划](doc/单元测试全覆盖计划-20260920-090603.md)；逐模块状态见 `feature_list.json`，源码与测试分类见 `unit-test-inventory.json`。

## Current State

- **Last Updated**：2026-09-27。
- **Current Objective**：为四个子仓库建立完整单元测试、集成测试与逐模块验收证据。
- **Active Item**：`unit-u2-sdk`，状态为 `in-progress`。U0 测试基线及 U1 base 已完成；U3—U9 未开始。
- SDK 当前 HEAD `18124c8`，全量离线单元基线 199/0/0/0，LINE 1948/1961、BRANCH 506/506、METHOD 441/452。宿主命令 `python3 verify-unit.py --mode baseline --scope metanet4j-sdk` 退出 0，证据 `evidence/20260926T164453Z/`。
- SDK 本地 HTTP 集成测试 5/0/0/0，证据 `evidence/20260926-u2-http/integration/`。HTTP 响应、BAP 加密、BOB/TXO 转换、公钥压缩与远程 Ordinal 的本轮定向报告见 `feature_list.json`。
- 八组仓库内历史 Ordinal 交易的固定向量及 Sigma 验签定向 8/0/0/0，证据 `evidence/20260927-u2-ord-fixtures-sigma-targeted/`。31 个旧 `external` 用例均已映射到真实存在的离线测试；需要实时 UTXO 或主网广播的部分另记人工原因。
- U1 base 严格验收 19/0/0/0，LINE 208/208、BRANCH 76/76、METHOD 51/51；证据 `evidence/20260926T072220Z/`。

## 阻塞与剩余工作

SDK 严格证据审计 `python3 verify-unit.py --mode accept --scope metanet4j-sdk --evidence evidence/20260926T164453Z` 退出 1，22 条检查项均为覆盖率缺口。剩余 13 行包括远程 Ordinal 公开转移入口 1 行、10 个无业务行为的隐式构造器，以及 `SigHashExtend` 固定内存流中不可触达的异常包装 2 行；分支覆盖已为 506/506。

远程 Ordinal 公开 `sendOrdinal(RemoteBapBase, …)` 的本地红测因 `KeyBag=null` 抛异常，证据 `evidence/20260927-u2-remote-send-red/`。该入口返回 `Transaction`，也无法交出待签摘要。胡先生已收到保留旧返回类型并新增准备入口、或修改旧入口返回类型的设计选择；依赖选择的改动暂缓。无行为及不可达字节码的严格验收口径也已请胡先生决定。

## Recommended Next Step

收到设计选择后修复远程转移入口，并按决定处理其余 12 行覆盖缺口，再执行 SDK 严格验收与 `./init.sh`。U2 达到计划完成条件后，依次推进 U3—U9。四仓库分支仍为 `feature/java25`，未推送。当前 `./init.sh` 退出 0，但共享中间件为 0 个运行容器；后续数据库等实连测试前须启动并核对连接与日志。
