#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/docs/likec4"
OUT="$SRC/dist"
WEB_ROOT="/var/www/pillbox-architecture"

docker run --rm \
  -u "$(id -u):$(id -g)" \
  -v "$SRC:/data" \
  likec4/likec4 \
  build -o /data/dist

sudo mkdir -p "$WEB_ROOT"
sudo rsync -a --delete "$OUT/" "$WEB_ROOT/"
sudo chown -R www-data:www-data "$WEB_ROOT"

echo "Готово: https://pi11box.ru ($WEB_ROOT)"
