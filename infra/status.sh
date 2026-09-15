#!/usr/bin/env bash
# 查看 ownword 研发共享中间件状态（容器 + 宿主机端口 + 各服务版本）。
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE="${DIR}/docker-compose.yml"

command -v docker >/dev/null 2>&1 || { echo "缺少命令：docker"; exit 1; }

echo "===== 容器状态 ====="
docker compose -f "${COMPOSE}" ps --format 'table {{.Name}}\t{{.Image}}\t{{.Status}}'

echo
echo "===== 端口监听 ====="
for spec in "27017:MongoDB" "9200:Elasticsearch" "9092:Kafka" "6379:Redis" "3306:MySQL"; do
  port="${spec%%:*}"
  name="${spec##*:}"
  if timeout 3 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/${port}" 2>/dev/null; then
    printf '%-16s %-6s 可连接\n' "${name}" "${port}"
  else
    printf '%-16s %-6s 不可连接\n' "${name}" "${port}"
  fi
done

echo
echo "===== 服务版本 ====="
printf 'MongoDB       '
docker exec infra-mongo mongosh --quiet --eval 'db.version()' 2>/dev/null || echo "(未运行)"
printf 'Elasticsearch '
docker exec infra-es curl -s localhost:9200 2>/dev/null | grep -o '"number" : "[^"]*"' || echo "(未运行)"
printf 'Redis         '
docker exec infra-redis redis-cli INFO server 2>/dev/null | grep -o 'redis_version:[0-9.]*' || echo "(未运行)"
printf 'MySQL         '
docker exec infra-mysql mysql -uroot -proot123 -N -e 'SELECT VERSION()' 2>/dev/null || echo "(未运行)"
printf 'Kafka         '
docker exec infra-kafka /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092 2>/dev/null | head -1 || echo "(未运行)"
