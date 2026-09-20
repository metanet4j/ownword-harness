# 当前进度

## Current State

环境准备已按用户“等下”指令暂停，当前比较 `ts-stack/packages/sdk` 与 Go SDK 作为 Java 移植参考。尚未批准或实施切换，事项不标记完成。

已建立四个 Java worktree，全部以各自 `feature/java25` 为起点；已复核 HEAD 与该分支相同，任务路径与四仓分支已采用 BSV 中性名称，精确基线见 `workspace.json`；生产源码与 POM 无改动。任务 Maven 缓存已复制约 485 MB 第三方依赖，排除了 `com/metanet4j`；未执行 Maven 构建和任何测试。

`reference/go-sdk` 只完成 `--no-checkout` 克隆，HEAD 已取得，工作文件尚未检出。Go 工具链未安装，TS 源码未克隆、依赖未安装。`init.sh` 是明确返回 2 的未就绪入口。

## Last Updated

2026-09-20，TypeScript 上游比较阶段。

## Current Objective

保留已创建的工作区，向用户说明 TypeScript 参考路线的适用性和剩余准备成本。

## Recommended Next Step

用户决定上游路线后更新准备计划和命名，完成对应源码固定、工具版本隔离、构建与离线冒烟。准备文件在根仓单独提交，环境未验收。
