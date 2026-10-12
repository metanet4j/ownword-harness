# 会话交接

## 当前任务

用户要求先修复 6 例输入重放缺口、25 例输入差异和 32 条未执行断言相关问题（32 条已按用户确认保留原样，并补独立有效 DRBG 分支验证），然后重新进行全量验收。当前事项为 `migration-input-replay`；本轮尚未通过验收。

当前状态与命令结果见 [progress.md](progress.md)，最终门禁状态见 [feature_list.json](feature_list.json)。

## 来源与环境

- 工作目录：`/home/haodev/ownword/_task/backend-worktree/bsv-sdk-java-migration`。
- SDK 分支：`feature/bsv-sdk-java-migration`；修复已提交，当前 HEAD 为 `6a5569a`，工作树干净。
- 固定 TS：`f999e0c1aad9a7afd0cbadaaf23841d049af9d5a`，只读。
- `./init.sh` 与宿主 `node audit-api.cjs batches` 已通过。
- Maven/pnpm 使用任务入口；Maven 与采集统一经 `./lock.sh` 串行执行。

## 必须保留的边界

原 TS 用例、原断言与原规模向量保持不变。补齐缺失输入必须来自 Java 实际消费的公开入口，不能复制 TS 实际输出或靠比较器放宽取得通过。

32 条未执行站点正在核对原测试控制流；真实不可达断言不能登记为已执行。跨语言实际输入须区分语义表示与真实重放差异，保留原始观测与独立比较表示。

## 验收执行

历史 `.cache/evidence/full-run-52-20260901/` 仅为基线。修复改变 SDK、工具或清单后必须重新生成证据。源码提交冻结后运行 `full-evidence-preflight.py`，随后 `full-evidence-run.py run` 单次串行完成 TS、Java、bundle 和 check；默认 90 分钟，只有真实同源超时来源才可采用 180 分钟重试。

当前常规 `clean test` 已 5451/5451 通过，HTTP 缺省运行与 Coordinator 通知顺序已修复，JAR 已安装任务缓存。清空 6 例缺口后额外发现并修复 4 条 expected 缺失，最新六例输入与 28 条原断言严格对照通过。全量阶段需无输入缺口、无输入替换豁免；32 条控制流不可达证明仍单列，独立 DRBG 回归不充抵原用例。

## 下一步

全量前检已就绪（5329 原例、38092 输入、56744 断言实例）。正式目录 `.cache/evidence/full-run-repaired-20261012/`；冻结工具后按 90 分钟上限运行单次双侧全量采集与终审，最后从通过的当前 clean test 产物安装 JAR 并核对全部交付。
