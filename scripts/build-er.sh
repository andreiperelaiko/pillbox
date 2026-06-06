#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/docs/er"
WEB_ROOT="/var/www/pillbox-er"

sudo mkdir -p "$WEB_ROOT"
sudo rsync -a --delete "$SRC/" "$WEB_ROOT/"
sudo chown -R www-data:www-data "$WEB_ROOT"

echo "Готово: https://pi11box.ru/er/ ($WEB_ROOT)"
