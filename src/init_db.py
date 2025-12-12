import sys
from pathlib import Path
from db import get_conn

def init_database():
    schema_file = Path(__file__).parent.parent / "schema.sql"
    
    if not schema_file.exists():
        print(f"Файл schema.sql не найден: {schema_file}")
        sys.exit(1)
    
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
                conn.commit()
                print("✅ База данных успешно инициализирована")
                    
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
