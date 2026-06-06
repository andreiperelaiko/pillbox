from pathlib import Path

from src.db import ensure_auth_schema, ensure_schedule_notification_schema, get_conn


def init_database() -> None:
    schema_file = Path(__file__).parent.parent / "schema.sql"
    with open(schema_file, encoding="utf-8") as f:
        schema_sql = f.read()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            conn.commit()
    ensure_auth_schema()
    ensure_schedule_notification_schema()
