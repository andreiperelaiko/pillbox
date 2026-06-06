import os
import secrets
from datetime import datetime, timedelta, timezone
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
            cur.execute(
                "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS telegram_sent_at TIMESTAMP WITH TIME ZONE"
            )
            _ensure_schedule_reminder_stats_table(conn)
            cur.execute(
                "ALTER TABLE medication_schedules ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE"
            )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS email_outbox (
                    id SERIAL PRIMARY KEY,
                    to_email VARCHAR(255) NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    body TEXT NOT NULL,
                    sent_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()


def ensure_medications_schema() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "ALTER TABLE medications ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE"
            )
            conn.commit()


def normalize_telegram_username(telegram: Optional[str]) -> Optional[str]:
    if telegram is None:
        return None
    value = telegram.strip().lstrip("@").lower()
    return value or None


def telegram_username_taken(telegram: str, exclude_user_id: Optional[int] = None) -> bool:
    normalized = normalize_telegram_username(telegram)
    if not normalized:
        return False
    existing = get_user_by_telegram(normalized)
    if not existing:
        return False
    if exclude_user_id is not None and existing["id"] == exclude_user_id:
        return False
    return True


def create_user(
    email: str,
    name: str,
    phone: Optional[str] = None,
    telegram: Optional[str] = None
) -> int:
    telegram = normalize_telegram_username(telegram)
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
                SELECT id, email, name, phone, telegram, telegram_chat_id, email_verified
                FROM users
                WHERE id = %s
            """, (user_id,))
            return cur.fetchone()


def get_user_by_telegram(telegram: str) -> Optional[Dict[str, Any]]:
    ensure_auth_schema()
    normalized = normalize_telegram_username(telegram)
    if not normalized:
        return None
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
    normalized = email.strip().lower()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, email, name, phone, telegram, telegram_chat_id, email_verified
                FROM users
                WHERE LOWER(email) = %s
            """, (normalized,))
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


def get_user_wards(guardian_id: int) -> List[Dict[str, Any]]:
    ensure_auth_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT u.id, u.email, u.name, u.phone, u.telegram, u.telegram_chat_id, ug.relationship
                FROM user_guardians ug
                JOIN users u ON ug.user_id = u.id
                WHERE ug.guardian_id = %s
            """, (guardian_id,))
            return cur.fetchall()


def remove_guardian_link(user_id: int, guardian_id: int) -> bool:
    ensure_guardian_invites_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM user_guardians
                WHERE user_id = %s AND guardian_id = %s
                RETURNING id
                """,
                (user_id, guardian_id),
            )
            row = cur.fetchone()
            if row:
                cur.execute(
                    """
                    UPDATE guardian_invites
                    SET status = 'revoked',
                        guardian_telegram_notified = FALSE,
                        patient_telegram_notified = FALSE,
                        guardian_approved = FALSE,
                        patient_approved = FALSE
                    WHERE patient_user_id = %s
                      AND guardian_user_id = %s
                      AND status = 'accepted'
                    """,
                    (user_id, guardian_id),
                )
            conn.commit()
            return row is not None


def guardian_link_exists(user_id: int, guardian_id: int) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM user_guardians
                WHERE user_id = %s AND guardian_id = %s
                """,
                (user_id, guardian_id),
            )
            return cur.fetchone() is not None


def ensure_guardian_invites_schema() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS guardian_invites (
                    id SERIAL PRIMARY KEY,
                    patient_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    guardian_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    relationship TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    guardian_telegram_notified BOOLEAN NOT NULL DEFAULT FALSE,
                    patient_telegram_notified BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(patient_user_id, guardian_user_id)
                )
                """
            )
            cur.execute(
                """
                ALTER TABLE guardian_invites
                ADD COLUMN IF NOT EXISTS guardian_telegram_notified BOOLEAN NOT NULL DEFAULT FALSE
                """
            )
            cur.execute(
                """
                ALTER TABLE guardian_invites
                ADD COLUMN IF NOT EXISTS patient_telegram_notified BOOLEAN NOT NULL DEFAULT FALSE
                """
            )
            cur.execute(
                """
                ALTER TABLE guardian_invites
                ADD COLUMN IF NOT EXISTS guardian_approved BOOLEAN NOT NULL DEFAULT FALSE
                """
            )
            cur.execute(
                """
                ALTER TABLE guardian_invites
                ADD COLUMN IF NOT EXISTS patient_approved BOOLEAN NOT NULL DEFAULT FALSE
                """
            )
            cur.execute(
                """
                ALTER TABLE guardian_invites
                ADD COLUMN IF NOT EXISTS initiated_by VARCHAR(20) NOT NULL DEFAULT 'guardian'
                """
            )
            cur.execute(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'guardian_invites'
                          AND column_name = 'telegram_notified'
                    ) THEN
                        UPDATE guardian_invites
                        SET guardian_telegram_notified = telegram_notified
                        WHERE guardian_telegram_notified = FALSE;
                        ALTER TABLE guardian_invites DROP COLUMN telegram_notified;
                    END IF;
                END $$
                """
            )
            conn.commit()


def invite_approver_party(initiated_by: str) -> str:
    return "patient" if initiated_by == "guardian" else "guardian"


def create_guardian_invite(
    patient_user_id: int,
    guardian_user_id: int,
    relationship: Optional[str] = None,
    initiated_by: str = "guardian",
) -> int:
    ensure_guardian_invites_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO guardian_invites (
                    patient_user_id, guardian_user_id, relationship, status, initiated_by
                )
                VALUES (%s, %s, %s, 'pending', %s)
                ON CONFLICT (patient_user_id, guardian_user_id) DO UPDATE
                SET relationship = EXCLUDED.relationship,
                    initiated_by = EXCLUDED.initiated_by,
                    status = CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM user_guardians ug
                            WHERE ug.user_id = guardian_invites.patient_user_id
                              AND ug.guardian_id = guardian_invites.guardian_user_id
                        ) THEN 'accepted'
                        ELSE 'pending'
                    END,
                    guardian_telegram_notified = FALSE,
                    patient_telegram_notified = FALSE
                RETURNING id
                """,
                (patient_user_id, guardian_user_id, relationship, initiated_by),
            )
            invite_id = cur.fetchone()[0]
            conn.commit()
            return invite_id


def get_guardian_invite(invite_id: int) -> Optional[Dict[str, Any]]:
    ensure_guardian_invites_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    gi.id,
                    gi.patient_user_id,
                    gi.guardian_user_id,
                    gi.relationship,
                    gi.status,
                    gi.guardian_telegram_notified,
                    gi.patient_telegram_notified,
                    gi.initiated_by,
                    p.name AS patient_name,
                    p.email AS patient_email,
                    p.telegram_chat_id AS patient_chat_id,
                    g.name AS guardian_name,
                    g.email AS guardian_email,
                    g.telegram_chat_id AS guardian_chat_id
                FROM guardian_invites gi
                JOIN users p ON p.id = gi.patient_user_id
                JOIN users g ON g.id = gi.guardian_user_id
                WHERE gi.id = %s
                """,
                (invite_id,),
            )
            return cur.fetchone()


def get_guardian_invites_to_notify() -> List[Dict[str, Any]]:
    ensure_guardian_invites_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    gi.id,
                    gi.patient_user_id,
                    gi.guardian_user_id,
                    gi.relationship,
                    gi.guardian_telegram_notified,
                    gi.patient_telegram_notified,
                    gi.initiated_by,
                    p.name AS patient_name,
                    p.telegram_chat_id AS patient_chat_id,
                    g.name AS guardian_name,
                    g.telegram_chat_id AS guardian_chat_id
                FROM guardian_invites gi
                JOIN users p ON p.id = gi.patient_user_id
                JOIN users g ON g.id = gi.guardian_user_id
                WHERE gi.status = 'pending'
                  AND (
                    (gi.guardian_telegram_notified = FALSE
                     AND g.telegram_chat_id IS NOT NULL)
                    OR
                    (gi.patient_telegram_notified = FALSE
                     AND p.telegram_chat_id IS NOT NULL)
                  )
                ORDER BY gi.id
                """
            )
            return cur.fetchall()


def mark_guardian_invite_party_notified(invite_id: int, party: str) -> None:
    ensure_guardian_invites_schema()
    column = (
        "guardian_telegram_notified"
        if party == "guardian"
        else "patient_telegram_notified"
    )
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE guardian_invites SET {column} = TRUE WHERE id = %s",
                (invite_id,),
            )
            conn.commit()


def _finalize_guardian_invite(
    cur,
    invite_id: int,
    patient_user_id: int,
    guardian_user_id: int,
    relationship: Optional[str],
) -> None:
    if not guardian_link_exists(patient_user_id, guardian_user_id):
        cur.execute(
            """
            INSERT INTO user_guardians (user_id, guardian_id, relationship)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, guardian_id) DO UPDATE
            SET relationship = EXCLUDED.relationship
            """,
            (patient_user_id, guardian_user_id, relationship),
        )
    cur.execute(
        "UPDATE guardian_invites SET status = 'accepted' WHERE id = %s",
        (invite_id,),
    )


def respond_to_guardian_invite(invite_id: int, user_id: int, approved: bool) -> str:
    """Ответ на приглашение. Подтверждает только второй участник (не инициатор)."""
    ensure_guardian_invites_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    gi.id,
                    gi.patient_user_id,
                    gi.guardian_user_id,
                    gi.relationship,
                    gi.status,
                    gi.initiated_by
                FROM guardian_invites gi
                WHERE gi.id = %s
                FOR UPDATE
                """,
                (invite_id,),
            )
            invite = cur.fetchone()
            if not invite or invite["status"] != "pending":
                return "not_found"

            initiated_by = invite["initiated_by"]
            approver_party = invite_approver_party(initiated_by)
            approver_user_id = (
                invite["patient_user_id"]
                if approver_party == "patient"
                else invite["guardian_user_id"]
            )

            if user_id != approver_user_id:
                return "not_approver"

            if not approved:
                cur.execute(
                    "UPDATE guardian_invites SET status = 'rejected' WHERE id = %s",
                    (invite_id,),
                )
                conn.commit()
                return "rejected"

            _finalize_guardian_invite(
                cur,
                invite_id,
                invite["patient_user_id"],
                invite["guardian_user_id"],
                invite.get("relationship"),
            )
            conn.commit()
            return "completed"


def accept_guardian_invite(invite_id: int, guardian_user_id: int) -> bool:
    """Тестовый хелпер: подтверждает тот, кому адресован запрос."""
    invite = get_guardian_invite(invite_id)
    if not invite:
        return False
    approver_id = (
        invite["patient_user_id"]
        if invite_approver_party(invite["initiated_by"]) == "patient"
        else invite["guardian_user_id"]
    )
    return respond_to_guardian_invite(invite_id, approver_id, True) == "completed"


def reject_guardian_invite(invite_id: int, user_id: int) -> bool:
    return respond_to_guardian_invite(invite_id, user_id, False) == "rejected"


def create_medication(
    name: str,
    description: Optional[str] = None,
    user_id: Optional[int] = None,
) -> int:
    ensure_medications_schema()
    if user_id is None:
        raise ValueError("user_id is required")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO medications (name, description, user_id)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (name, description, user_id))
            medication_id = cur.fetchone()[0]
            conn.commit()
            return medication_id


def get_medications(user_id: int) -> List[Dict[str, Any]]:
    ensure_medications_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, name, description
                FROM medications
                WHERE user_id = %s
                ORDER BY name
            """, (user_id,))
            return cur.fetchall()


def get_medication(medication_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    ensure_medications_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if user_id is None:
                cur.execute("""
                    SELECT id, name, description
                    FROM medications
                    WHERE id = %s
                """, (medication_id,))
            else:
                cur.execute("""
                    SELECT id, name, description
                    FROM medications
                    WHERE id = %s AND user_id = %s
                """, (medication_id, user_id))
            return cur.fetchone()


def delete_medication(medication_id: int, user_id: int) -> bool:
    ensure_medications_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM medications
                WHERE id = %s AND user_id = %s
                RETURNING id
                """,
                (medication_id, user_id),
            )
            row = cur.fetchone()
            conn.commit()
            return row is not None


def create_schedule(
    medication_id: int,
    intake_at: datetime,
    dose: Optional[str] = None,
    user_id: Optional[int] = None,
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
                    INSERT INTO medication_schedules (medication_id, intake_at, dose, time, user_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (medication_id, intake_at, dose, intake_at.time(), user_id),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO medication_schedules (medication_id, intake_at, dose, user_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (medication_id, intake_at, dose, user_id),
                )
            schedule_id = cur.fetchone()[0]
            conn.commit()
            return schedule_id


def get_medication_schedules(medication_id: int, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if user_id is None:
                cur.execute("""
                    SELECT id, medication_id, intake_at, taken, dose
                    FROM medication_schedules
                    WHERE medication_id = %s
                    ORDER BY intake_at
                """, (medication_id,))
            else:
                cur.execute("""
                    SELECT id, medication_id, intake_at, taken, dose
                    FROM medication_schedules
                    WHERE medication_id = %s AND user_id = %s
                    ORDER BY intake_at
                """, (medication_id, user_id))
            return cur.fetchall()


def log_medication_taken(
    schedule_id: int,
    user_id: Optional[int] = None,
) -> int:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            if user_id is None:
                cur.execute("""
                    UPDATE medication_schedules
                    SET taken = TRUE
                    WHERE id = %s
                    RETURNING id
                """, (schedule_id,))
            else:
                cur.execute("""
                    UPDATE medication_schedules
                    SET taken = TRUE
                    WHERE id = %s AND user_id = %s
                    RETURNING id
                """, (schedule_id, user_id))
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else 0


def delete_schedule(
    schedule_id: int,
    user_id: int,
    medication_id: Optional[int] = None,
) -> bool:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            if medication_id is None:
                cur.execute(
                    """
                    DELETE FROM medication_schedules
                    WHERE id = %s AND user_id = %s
                    RETURNING id
                    """,
                    (schedule_id, user_id),
                )
            else:
                cur.execute(
                    """
                    DELETE FROM medication_schedules
                    WHERE id = %s AND user_id = %s AND medication_id = %s
                    RETURNING id
                    """,
                    (schedule_id, user_id, medication_id),
                )
            row = cur.fetchone()
            conn.commit()
            return row is not None


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
                WHERE ms.user_id = %s
            """
            params: List[Any] = [user_id]

            if days:
                query += " AND ms.intake_at >= CURRENT_DATE - INTERVAL %s"
                params.append(f"{days} days")
            
            query += " ORDER BY ms.intake_at DESC"
            
            cur.execute(query, params)
            return cur.fetchall()


def _ensure_schedule_reminder_stats_table(conn=None) -> None:
    own_conn = conn is None
    if own_conn:
        conn = get_conn().__enter__()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS schedule_reminder_stats (
                    schedule_id INTEGER NOT NULL
                        REFERENCES medication_schedules(id) ON DELETE CASCADE,
                    recipient_user_id INTEGER NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
                    sent_count INTEGER NOT NULL DEFAULT 0,
                    last_sent_at TIMESTAMP WITH TIME ZONE,
                    PRIMARY KEY (schedule_id, recipient_user_id)
                )
                """
            )
            if own_conn:
                conn.commit()
    finally:
        if own_conn:
            conn.__exit__(None, None, None)


def ensure_schedule_reminder_stats_schema() -> None:
    _ensure_schedule_reminder_stats_table()


def get_reminder_sent_count(schedule_id: int, recipient_user_id: int) -> int:
    ensure_schedule_reminder_stats_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sent_count
                FROM schedule_reminder_stats
                WHERE schedule_id = %s AND recipient_user_id = %s
                """,
                (schedule_id, recipient_user_id),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0


def record_reminder_sent(schedule_id: int, recipient_user_id: int) -> int:
    ensure_schedule_reminder_stats_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO schedule_reminder_stats (
                    schedule_id, recipient_user_id, sent_count, last_sent_at
                )
                VALUES (%s, %s, 1, CURRENT_TIMESTAMP)
                ON CONFLICT (schedule_id, recipient_user_id) DO UPDATE
                SET sent_count = schedule_reminder_stats.sent_count + 1,
                    last_sent_at = CURRENT_TIMESTAMP
                RETURNING sent_count
                """,
                (schedule_id, recipient_user_id),
            )
            sent_count = cur.fetchone()[0]
            conn.commit()
            return int(sent_count)


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
                SELECT
                    n.id,
                    n.schedule_id,
                    n.guardian_id,
                    n.text,
                    CASE
                        WHEN n.guardian_id IS NOT NULL THEN g.telegram_chat_id
                        ELSE p.telegram_chat_id
                    END AS telegram_chat_id
                FROM notifications n
                JOIN medication_schedules ms ON ms.id = n.schedule_id
                JOIN users p ON p.id = ms.user_id
                LEFT JOIN users g ON g.id = n.guardian_id
                WHERE n.telegram_sent_at IS NULL
                  AND (
                    (n.guardian_id IS NOT NULL AND g.telegram_chat_id IS NOT NULL)
                    OR (n.guardian_id IS NULL AND p.telegram_chat_id IS NOT NULL)
                  )
                ORDER BY n.id
            """)
            return cur.fetchall()


def mark_notification_sent(notification_id: int) -> int:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE notifications
                SET telegram_sent_at = CURRENT_TIMESTAMP
                WHERE id = %s AND telegram_sent_at IS NULL
                """,
                (notification_id,),
            )
            updated = cur.rowcount
            conn.commit()
            return updated


def delete_notification(notification_id: int) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
            deleted = cur.rowcount
            conn.commit()
            return deleted


def get_due_reminders(
    delay_minutes: int = 1,
    max_reminders: int = 3,
) -> List[Dict[str, Any]]:
    """Приёмы, по которым пора отправить следующее напоминание (до max_reminders на получателя)."""
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                WITH recipients AS (
                    SELECT
                        ms.id AS schedule_id,
                        ms.medication_id,
                        ms.intake_at,
                        ms.dose,
                        ms.user_id,
                        m.name AS medication_name,
                        u.name AS user_name,
                        u.email AS user_email,
                        NULL::int AS guardian_id,
                        u.id AS recipient_user_id,
                        u.email AS recipient_email,
                        COALESCE(srs.sent_count, 0) AS sent_count,
                        srs.last_sent_at
                    FROM medication_schedules ms
                    JOIN medications m ON m.id = ms.medication_id
                    JOIN users u ON u.id = ms.user_id
                    LEFT JOIN schedule_reminder_stats srs
                        ON srs.schedule_id = ms.id
                       AND srs.recipient_user_id = u.id
                    WHERE ms.taken = FALSE
                      AND ms.user_id IS NOT NULL

                    UNION ALL

                    SELECT
                        ms.id AS schedule_id,
                        ms.medication_id,
                        ms.intake_at,
                        ms.dose,
                        ms.user_id,
                        m.name AS medication_name,
                        u.name AS user_name,
                        u.email AS user_email,
                        g.id AS guardian_id,
                        g.id AS recipient_user_id,
                        g.email AS recipient_email,
                        COALESCE(srs.sent_count, 0) AS sent_count,
                        srs.last_sent_at
                    FROM medication_schedules ms
                    JOIN medications m ON m.id = ms.medication_id
                    JOIN users u ON u.id = ms.user_id
                    JOIN user_guardians ug ON ug.user_id = ms.user_id
                    JOIN users g ON g.id = ug.guardian_id
                    LEFT JOIN schedule_reminder_stats srs
                        ON srs.schedule_id = ms.id
                       AND srs.recipient_user_id = g.id
                    WHERE ms.taken = FALSE
                      AND ms.user_id IS NOT NULL
                )
                SELECT *
                FROM recipients
                WHERE sent_count < %s
                  AND (
                    (sent_count = 0
                     AND intake_at <= NOW() - (%s * INTERVAL '1 minute'))
                    OR
                    (sent_count > 0
                     AND last_sent_at <= NOW() - (%s * INTERVAL '1 minute'))
                  )
                ORDER BY intake_at, guardian_id NULLS FIRST
                """,
                (max_reminders, delay_minutes, delay_minutes),
            )
            return cur.fetchall()


def get_overdue_schedules(grace_minutes: int = 1) -> List[Dict[str, Any]]:
    """Обратная совместимость: первое напоминание после grace_minutes."""
    return get_due_reminders(delay_minutes=grace_minutes, max_reminders=1)


def queue_email(to_email: str, subject: str, body: str) -> int:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO email_outbox (to_email, subject, body)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (to_email, subject, body),
            )
            email_id = cur.fetchone()[0]
            conn.commit()
            return email_id


def get_pending_emails(limit: int = 50) -> List[Dict[str, Any]]:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, to_email, subject, body
                FROM email_outbox
                WHERE sent_at IS NULL
                ORDER BY id
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()


def mark_email_sent(email_id: int) -> int:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE email_outbox
                SET sent_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (email_id,),
            )
            updated = cur.rowcount
            conn.commit()
            return updated


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
            cur.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE"
            )
            cur.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token TEXT"
            )
            cur.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_expires_at TIMESTAMP WITH TIME ZONE"
            )
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
            cur.execute("ALTER TABLE user_guardians ADD COLUMN IF NOT EXISTS relationship TEXT")
            cur.execute(
                """
                UPDATE users
                SET telegram = LOWER(LTRIM(telegram, '@'))
                WHERE telegram IS NOT NULL
                """
            )
            cur.execute(
                """
                WITH ranked AS (
                    SELECT
                        id,
                        ROW_NUMBER() OVER (
                            PARTITION BY LOWER(LTRIM(telegram, '@'))
                            ORDER BY id
                        ) AS rn
                    FROM users
                    WHERE telegram IS NOT NULL AND telegram <> ''
                )
                UPDATE users AS u
                SET telegram = NULL, telegram_chat_id = NULL
                FROM ranked
                WHERE u.id = ranked.id AND ranked.rn > 1
                """
            )
            cur.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = 'users_telegram_unique'
                    ) THEN
                        ALTER TABLE users
                        ADD CONSTRAINT users_telegram_unique UNIQUE (telegram);
                    END IF;
                END $$
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
    telegram = normalize_telegram_username(telegram)
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


def update_user_telegram(user_id: int, telegram: Optional[str]) -> bool:
    ensure_auth_schema()
    normalized = normalize_telegram_username(telegram)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET telegram = %s, telegram_chat_id = NULL
                WHERE id = %s
                RETURNING id
                """,
                (normalized, user_id),
            )
            row = cur.fetchone()
            conn.commit()
            return row is not None


def create_email_verification_token(user_id: int, hours: int = 24) -> str:
    ensure_auth_schema()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET email_verification_token = %s,
                    email_verification_expires_at = %s
                WHERE id = %s
                RETURNING id
                """,
                (token, expires_at, user_id),
            )
            if not cur.fetchone():
                raise ValueError("User not found")
            conn.commit()
    return token


def verify_email_by_token(token: str) -> Optional[int]:
    ensure_auth_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET email_verified = TRUE,
                    email_verification_token = NULL,
                    email_verification_expires_at = NULL
                WHERE email_verification_token = %s
                  AND email_verification_expires_at > NOW()
                RETURNING id
                """,
                (token,),
            )
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else None


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
                SELECT u.id, u.email, u.name, u.phone, u.telegram, u.telegram_chat_id, u.email_verified
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
