import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import psycopg
from psycopg.rows import dict_row


def get_conn():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg.connect(database_url)
    
    dbname = os.getenv("POSTGRES_DB", "pillboxdb")
    user = os.getenv("POSTGRES_USER", "pillbox")
    password = os.getenv("POSTGRES_PASSWORD", "password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    
    return psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )


def ensure_schedule_notification_schema() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE medication_schedules ADD COLUMN IF NOT EXISTS intake_at TIMESTAMP WITH TIME ZONE")
            cur.execute("ALTER TABLE medication_schedules ADD COLUMN IF NOT EXISTS taken BOOLEAN NOT NULL DEFAULT FALSE")
            cur.execute("ALTER TABLE medication_schedules ADD COLUMN IF NOT EXISTS dose TEXT")
            cur.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'medication_schedules' AND column_name = 'taken_at'
                """
            )
            if cur.fetchone() is not None:
                cur.execute("UPDATE medication_schedules SET taken = TRUE WHERE taken_at IS NOT NULL")
                cur.execute("ALTER TABLE medication_schedules DROP COLUMN IF EXISTS taken_at")
            cur.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS schedule_id INTEGER")
            cur.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS text TEXT")
            cur.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS type VARCHAR(50)")
            cur.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS title VARCHAR(255)")
            cur.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS message TEXT")
            cur.execute("ALTER TABLE notifications ALTER COLUMN type SET DEFAULT 'system'")
            cur.execute("ALTER TABLE notifications ALTER COLUMN title SET DEFAULT ''")
            cur.execute("ALTER TABLE notifications ALTER COLUMN message SET DEFAULT ''")
            cur.execute("ALTER TABLE notifications ALTER COLUMN text SET DEFAULT ''")
            conn.commit()


def ensure_medications_schema() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE medications DROP COLUMN IF EXISTS user_id")
            conn.commit()


def create_user(
    email: str,
    name: str,
    phone: Optional[str] = None,
    telegram: Optional[str] = None
) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (email, name, phone, telegram)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (email, name, phone, telegram))
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    ensure_auth_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, email, name, phone, telegram, telegram_chat_id
                FROM users
                WHERE id = %s
            """, (user_id,))
            return cur.fetchone()


def get_user_by_telegram(telegram: str) -> Optional[Dict[str, Any]]:
    ensure_auth_schema()
    normalized = telegram.lower().lstrip("@")
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, email, name, phone, telegram, telegram_chat_id
                FROM users
                WHERE LOWER(REPLACE(telegram, '@', '')) = %s
            """, (normalized,))
            return cur.fetchone()


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    ensure_auth_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, email, name, phone, telegram, telegram_chat_id
                FROM users
                WHERE email = %s
            """, (email,))
            return cur.fetchone()


def add_guardian(
    user_id: int,
    guardian_id: int,
    relationship: Optional[str] = None
) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_guardians (user_id, guardian_id, relationship)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (user_id, guardian_id, relationship))
            link_id = cur.fetchone()[0]
            conn.commit()
            return link_id


def get_user_guardians(user_id: int) -> List[Dict[str, Any]]:
    ensure_auth_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT u.id, u.email, u.name, u.phone, u.telegram, u.telegram_chat_id, ug.relationship
                FROM user_guardians ug
                JOIN users u ON ug.guardian_id = u.id
                WHERE ug.user_id = %s
            """, (user_id,))
            return cur.fetchall()


def create_medication(
    name: str,
    description: Optional[str] = None,
) -> int:
    ensure_medications_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO medications (name, description)
                VALUES (%s, %s)
                RETURNING id
            """, (name, description))
            medication_id = cur.fetchone()[0]
            conn.commit()
            return medication_id


def get_medications() -> List[Dict[str, Any]]:
    ensure_medications_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, name, description
                FROM medications
                ORDER BY name
            """)
            return cur.fetchall()


def get_medication(medication_id: int) -> Optional[Dict[str, Any]]:
    ensure_medications_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, name, description
                FROM medications
                WHERE id = %s
            """, (medication_id,))
            return cur.fetchone()


def create_schedule(
    medication_id: int,
    intake_at: datetime,
    dose: Optional[str] = None,
) -> int:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'medication_schedules' AND column_name = 'time'
                """
            )
            has_time_col = cur.fetchone() is not None
            if has_time_col:
                cur.execute(
                    """
                    INSERT INTO medication_schedules (medication_id, intake_at, dose, time)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (medication_id, intake_at, dose, intake_at.time()),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO medication_schedules (medication_id, intake_at, dose)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (medication_id, intake_at, dose),
                )
            schedule_id = cur.fetchone()[0]
            conn.commit()
            return schedule_id


def get_medication_schedules(medication_id: int) -> List[Dict[str, Any]]:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, medication_id, intake_at, taken, dose
                FROM medication_schedules
                WHERE medication_id = %s
                ORDER BY intake_at
            """, (medication_id,))
            return cur.fetchall()


def log_medication_taken(
    schedule_id: int,
) -> int:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE medication_schedules
                SET taken = TRUE
                WHERE id = %s
                RETURNING id
            """, (schedule_id,))
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else 0


def log_medication_missed(
    schedule_id: int,
) -> int:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE medication_schedules
                SET taken = FALSE
                WHERE id = %s
                RETURNING id
            """, (schedule_id,))
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else 0


def get_medication_history(
    medication_id: int,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            query = """
                SELECT id, medication_id, intake_at AS scheduled_time, taken, dose
                FROM medication_schedules
                WHERE medication_id = %s
                ORDER BY intake_at DESC
            """
            if limit:
                query += f" LIMIT {limit}"
            
            cur.execute(query, (medication_id,))
            return cur.fetchall()


def get_user_medication_history(
    user_id: int,
    days: Optional[int] = None
) -> List[Dict[str, Any]]:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            query = """
                SELECT ms.id, ms.medication_id,
                       ms.intake_at AS scheduled_time, ms.taken, ms.dose,
                       m.name as medication_name
                FROM medication_schedules ms
                JOIN medications m ON ms.medication_id = m.id
                WHERE 1 = 1
            """
            params: List[Any] = []
            
            if days:
                query += " AND ms.intake_at >= CURRENT_DATE - INTERVAL %s"
                params.append(f"{days} days")
            
            query += " ORDER BY ms.intake_at DESC"
            
            cur.execute(query, params)
            return cur.fetchall()


def create_notification(
    schedule_id: int,
    text: str,
    guardian_id: Optional[int] = None,
) -> int:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO notifications (schedule_id, guardian_id, text)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (schedule_id, guardian_id, text))
            notification_id = cur.fetchone()[0]
            conn.commit()
            return notification_id


def get_user_notifications(
    user_id: int,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            query = """
                SELECT n.id, n.schedule_id, n.guardian_id, n.text
                FROM notifications n
                WHERE n.guardian_id = %s
                ORDER BY n.id DESC
            """
            if limit:
                query += f" LIMIT {limit}"
            
            cur.execute(query, (user_id,))
            return cur.fetchall()


def get_pending_notifications() -> List[Dict[str, Any]]:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT n.id, n.schedule_id, n.guardian_id, n.text,
                       u.telegram_chat_id
                FROM notifications n
                JOIN users u ON u.id = n.guardian_id
                WHERE u.telegram_chat_id IS NOT NULL
                ORDER BY n.id
            """)
            return cur.fetchall()


def delete_notification(notification_id: int) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
            deleted = cur.rowcount
            conn.commit()
            return deleted


def test_query():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            print(cur.fetchone())


def ensure_auth_schema() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT")
            cur.execute("ALTER TABLE users DROP COLUMN IF EXISTS telegram_verified")
            cur.execute("ALTER TABLE users DROP COLUMN IF EXISTS telegram_verification_code")
            cur.execute("ALTER TABLE users DROP COLUMN IF EXISTS telegram_verification_expires_at")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()


def create_user_with_password(
    email: str,
    name: str,
    password_hash: str,
    phone: Optional[str] = None,
    telegram: Optional[str] = None,
) -> int:
    ensure_auth_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, phone, telegram, password_hash)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (email, name, phone, telegram, password_hash),
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id


def get_auth_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    ensure_auth_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, email, name, phone, telegram, telegram_chat_id, password_hash
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            return cur.fetchone()


def save_telegram_chat_id(user_id: int, chat_id: str) -> int:
    ensure_auth_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET telegram_chat_id = %s
                WHERE id = %s
                RETURNING id
                """,
                (chat_id, user_id),
            )
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else 0


def create_session(session_id: str, user_id: int, expires_at: datetime) -> str:
    ensure_auth_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessions (id, user_id, expires_at)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (session_id, user_id, expires_at),
            )
            created_id = cur.fetchone()[0]
            conn.commit()
            return created_id


def get_user_by_session(session_id: str) -> Optional[Dict[str, Any]]:
    ensure_auth_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT u.id, u.email, u.name, u.phone, u.telegram, u.telegram_chat_id
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.id = %s AND s.expires_at > NOW()
                """,
                (session_id,),
            )
            return cur.fetchone()


def delete_session(session_id: str) -> int:
    ensure_auth_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
            deleted = cur.rowcount
            conn.commit()
            return deleted


def delete_user_sessions(user_id: int) -> int:
    ensure_auth_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
            deleted = cur.rowcount
            conn.commit()
            return deleted
