#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/music-bot}"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "Docker Compose не найден. Установите docker compose plugin или docker-compose." >&2
  exit 1
fi

cd "$PROJECT_DIR"

if [[ ! -f .env ]]; then
  echo "Файл .env не найден в $PROJECT_DIR" >&2
  echo "Скопируйте .env.example в .env и заполните BOT_TOKEN, ADMIN_ID и другие параметры." >&2
  exit 1
fi

mkdir -p cache logs secrets

"${COMPOSE_CMD[@]}" down --remove-orphans
"${COMPOSE_CMD[@]}" build --pull
"${COMPOSE_CMD[@]}" up -d

echo
echo "Сервисы подняты. Текущий статус:"
"${COMPOSE_CMD[@]}" ps
echo
echo "Последние логи бота:"
"${COMPOSE_CMD[@]}" logs --tail=50 bot