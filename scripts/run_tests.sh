#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Всегда тестовая БД — никогда не подхватывать DATABASE_URL из .env / окружения.
export DATABASE_URL="postgresql://pillbox_test:pillbox_test@localhost:5433/pillbox_test"
export SESSION_COOKIE_PATH=/
export SCHEDULER_GRACE_MINUTES=1
export SCHEDULER_MAX_REMINDERS=3

if ! docker compose -f docker-compose.test.yml ps --status running db 2>/dev/null | grep -q db; then
  docker compose -f docker-compose.test.yml up -d db
  echo "Ждём тестовую БД..."
  sleep 3
fi

uv run --extra dev pytest "$@"
