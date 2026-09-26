# session-handoff.md — 会话交接

## 当前任务

胡先生要求四个子仓库建立完整单元测试与集成测试，并已确认通过公开 API 测试；MongoDB、ES、MySQL、Kafka、Redis、文件和 HTTP 边界实测，公网服务本地模拟，自动测试不广播主网。原 Boot 4 / Java 25 升级已完成；当前 `unit-u1-base` 开始，U0 基线已完成。

开始工作时读取 `../AGENTS.md`、`../mvn-command.md`、本目录 `AGENTS.md`、[测试计划](doc/单元测试全覆盖计划-20260920-090603.md)、`feature_list.json`，再运行 `./init.sh`。遵守单功能项实施、提交和测试门禁；不读取 Archive，不推送，不修改四仓基线。

## U0 已确认的事实

parent `4112a48` 已提供 JaCoCo 0.8.14 `unit-coverage` profile。`unit-test-inventory.json` 列明 25 POM、369 生产 Java、53 测试 Java，测试执行安全分类与 19 项集成边界。sdk 的 Bitails 公网测试已标 `external`；component 的 Spring 基类、ES 和 SSE 类已标 `integration`。`verify-unit.py` 真实运行全仓基线：四仓 Maven 均成功，56 测试通过、8 跳过；入口因缺口退出 1。原始证据 `evidence/20260926T064228Z/`；严格检查发现 17 个可执行模块零测试、255 项类级覆盖缺口、54 个外部用例待映射、1 个非 void 测试。`component-core` 无实现，N/A。详见[测试基线](doc/测试基线与障碍-20260926-145423.md)。五类证据反例在 `evidence/20260926-u0-pilot/`。宿主五服务健康。

base 的 UTXO 相等性缺陷已通过红灯测试复现、绿灯修复并提交 `bae7eb6`；统一入口新基线 `evidence/20260926T070148Z/`，4/0/0/0。

## 下一步

按 U1 在 base 加公开 API 的有断言单元测试，先看真实 JaCoCo 行/分支，再逐行为测试，达到行、分支、方法 100% 后提交并安装产物，随后 U2 sdk。base 当前 4 个测试，行 50/222、分支 12/76、方法 10/55。注意 AipHelper 不可达 IOException 包装、BapHelper 固定算法异常路径；不能伪造输入凑覆盖。U0 的 sdk/component 测试标签已分别提交；任务文档按 ownword 主仓单独提交，仅提交本任务文件。

后续集成测试运行前核对 `infra/README-*.md` 的连接参数、`docker logs` 与应用日志、Surefire XML；宿主提权运行。先修 `EsTest` 固定索引和 `DefaultCompleteTxFactory` 硬编码广播路径，保持资源隔离。
