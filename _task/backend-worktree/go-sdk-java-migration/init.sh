#!/usr/bin/env bash
# 环境准备暂停期间明确拒绝报告通过，避免执行尚未完成的模板入口。
set -euo pipefail
printf '%s\n' '环境准备尚未完成；用户已暂停准备，正在比较 TypeScript 与 Go 上游。' >&2
printf '%s\n' '四个 Java worktree 已建立，构建与测试尚未执行。参见 session-handoff.md。' >&2
exit 2
