#!/usr/bin/env bash
# 启动 ownword 研发共享中间件，并等待全部就绪。
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE="${DIR}/docker-compose.yml"

command -v docker >/dev/null 2>&1 || { echo "缺少命令：docker"; exit 1; }

echo "[$(date '+%F %T')] 启动 ownword 共享中间件"
docker compose -f "${COMPOSE}" up -d

echo "[$(date '+%F %T')] 等待就绪（最多 180s）"
for _ in $(seq 1 36); do
  healthy="$(docker ps --filter label=com.docker.compose.project=ownword-infra --format '{{.Status}}' | grep -c healthy || true)"
  if [ "${healthy}" -ge 5 ]; then
    echo "[$(date '+%F %T')] 全部 healthy"
    docker compose -f "${COMPOSE}" ps --format 'table {{.Name}}\t{{.Status}}'
    exit 0
  fi
  sleep 5
done

echo "[$(date '+%F %T')] 超时：未在 180s 内全部 healthy"
docker compose -f "${COMPOSE}" ps --format 'table {{.Name}}\t{{.Status}}'
exit 1
