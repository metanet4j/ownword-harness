#!/usr/bin/env bash
# 停止 ownword 研发共享中间件。
#   默认：停止容器，保留数据卷
#   -v  ：同时删除数据卷（彻底重置，数据不可恢复）
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE="${DIR}/docker-compose.yml"

command -v docker >/dev/null 2>&1 || { echo "缺少命令：docker"; exit 1; }

if [ "${1:-}" = "-v" ]; then
  echo "[$(date '+%F %T')] 停止共享中间件并删除数据卷"
  docker compose -f "${COMPOSE}" down -v
else
  echo "[$(date '+%F %T')] 停止共享中间件（保留数据卷）"
  docker compose -f "${COMPOSE}" down
fi
