#!/usr/bin/env python3
"""Проверка подключения к БД Pillbox и выполнение SQL."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def mask_url(url: str) -> str:
    if "@" not in url:
        return url
    creds, rest = url.rsplit("@", 1)
    if "://" in creds:
        scheme, _, _userpass = creds.partition("://")
        return f"{scheme}://***@{rest}"
    return f"***@{rest}"


def resolve_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    user = os.getenv("POSTGRES_USER", "pillbox")
    password = os.getenv("POSTGRES_PASSWORD", "password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("POSTGRES_DB", "pillboxdb")
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def connect_check() -> None:
    from src.db import get_conn

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()")
            db, user, host, port = cur.fetchone()
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]

            print("Подключение успешно")
            print(f"  database: {db}")
            print(f"  user:     {user}")
            print(f"  host:     {host or 'local'}")
            print(f"  port:     {port or '-'}")
            print(f"  version:  {version.split(',')[0]}")

            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
            print(f"  tables:   {', '.join(tables) if tables else '(нет)'}")


def run_query(sql: str) -> None:
    from psycopg.rows import dict_row

    from src.db import get_conn

    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql)
            if cur.description is None:
                conn.commit()
                print(f"OK ({cur.rowcount} rows affected)")
                return

            rows = cur.fetchall()
            if not rows:
                print("(нет строк)")
                return

            cols = list(rows[0].keys())
            widths = {
                col: max(len(col), *(len(str(row.get(col, ""))) for row in rows))
                for col in cols
            }
            header = " | ".join(col.ljust(widths[col]) for col in cols)
            print(header)
            print("-+-".join("-" * widths[col] for col in cols))
            for row in rows:
                print(" | ".join(str(row.get(col, "")).ljust(widths[col]) for col in cols))


def open_psql() -> int:
    import shutil
    import subprocess

    psql = shutil.which("psql")
    if not psql:
        print("psql не найден. Установите postgresql-client или используйте -c SQL.", file=sys.stderr)
        return 1

    return subprocess.call([psql, resolve_database_url()])


def main() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    load_dotenv()

    parser = argparse.ArgumentParser(description="Подключение к БД Pillbox")
    parser.add_argument("-c", "--command", metavar="SQL", help="Выполнить SQL-запрос")
    parser.add_argument("--psql", action="store_true", help="Открыть интерактивный psql")
    parser.add_argument("--url", action="store_true", help="Показать строку подключения (пароль скрыт)")
    args = parser.parse_args()

    if args.url:
        print(mask_url(resolve_database_url()))
        return 0

    if args.psql:
        return open_psql()

    try:
        if args.command:
            run_query(args.command)
        else:
            connect_check()
    except Exception as exc:
        print(f"Ошибка подключения: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
