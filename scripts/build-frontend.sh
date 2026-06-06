#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND="$ROOT/frontend"
WEB_ROOT="/var/www/pillbox-frontend/site"

cd "$FRONTEND"
if command -v npm >/dev/null 2>&1; then
  npm ci
  npm run build
else
  docker run --rm -u "$(id -u):$(id -g)" -v "$FRONTEND:/app" -w /app node:20-alpine sh -c "npm ci && npm run build"
fi

sudo mkdir -p "$WEB_ROOT"
sudo rsync -a --delete dist/ "$WEB_ROOT/"
sudo chown -R www-data:www-data /var/www/pillbox-frontend

echo "Готово: https://pi11box.ru/site/ ($WEB_ROOT)"
