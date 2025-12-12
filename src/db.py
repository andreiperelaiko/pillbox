import os
from datetime import datetime, time, date
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
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, email, name, phone, telegram
                FROM users
                WHERE id = %s
            """, (user_id,))
            return cur.fetchone()


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, email, name, phone, telegram
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
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT u.id, u.email, u.name, u.phone, u.telegram, ug.relationship
                FROM user_guardians ug
                JOIN users u ON ug.guardian_id = u.id
                WHERE ug.user_id = %s
            """, (user_id,))
            return cur.fetchall()


def create_medication(
    user_id: int,
    name: str,
    description: Optional[str] = None,
    dosage: Optional[str] = None,
    unit: Optional[str] = None,
    quantity: Optional[int] = None
) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO medications (user_id, name, description, dosage, unit, quantity)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user_id, name, description, dosage, unit, quantity))
            medication_id = cur.fetchone()[0]
            conn.commit()
            return medication_id


def get_user_medications(user_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, user_id, name, description, dosage, unit, quantity
                FROM medications
                WHERE user_id = %s
                ORDER BY name
            """, (user_id,))
            return cur.fetchall()


def get_medication(medication_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, user_id, name, description, dosage, unit, quantity
                FROM medications
                WHERE id = %s
            """, (medication_id,))
            return cur.fetchone()


def create_schedule(
    medication_id: int,
    time: time
) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO medication_schedules (medication_id, time)
                VALUES (%s, %s)
                RETURNING id
            """, (medication_id, time))
            schedule_id = cur.fetchone()[0]
            conn.commit()
            return schedule_id


def get_medication_schedules(medication_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, medication_id, time
                FROM medication_schedules
                WHERE medication_id = %s
                ORDER BY time
            """, (medication_id,))
            return cur.fetchall()


def log_medication_taken(
    medication_id: int,
    scheduled_time: datetime,
    taken_at: Optional[datetime] = None,
    schedule_id: Optional[int] = None
) -> int:
    if taken_at is None:
        taken_at = datetime.now()
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO medication_logs 
                    (medication_id, schedule_id, scheduled_time, taken_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (medication_id, schedule_id, scheduled_time, taken_at))
            log_id = cur.fetchone()[0]
            conn.commit()
            return log_id


def log_medication_missed(
    medication_id: int,
    scheduled_time: datetime,
    schedule_id: Optional[int] = None
) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO medication_logs 
                    (medication_id, schedule_id, scheduled_time, taken_at)
                VALUES (%s, %s, %s, NULL)
                RETURNING id
            """, (medication_id, schedule_id, scheduled_time))
            log_id = cur.fetchone()[0]
            conn.commit()
            return log_id


def get_medication_history(
    medication_id: int,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            query = """
                SELECT id, medication_id, schedule_id, scheduled_time, taken_at
                FROM medication_logs
                WHERE medication_id = %s
                ORDER BY scheduled_time DESC
            """
            if limit:
                query += f" LIMIT {limit}"
            
            cur.execute(query, (medication_id,))
            return cur.fetchall()


def get_user_medication_history(
    user_id: int,
    days: Optional[int] = None
) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            query = """
                SELECT ml.id, ml.medication_id, ml.schedule_id, 
                       ml.scheduled_time, ml.taken_at,
                       m.name as medication_name
                FROM medication_logs ml
                JOIN medications m ON ml.medication_id = m.id
                WHERE m.user_id = %s
            """
            params = [user_id]
            
            if days:
                query += " AND ml.scheduled_time >= CURRENT_DATE - INTERVAL %s"
                params.append(f"{days} days")
            
            query += " ORDER BY ml.scheduled_time DESC"
            
            cur.execute(query, params)
            return cur.fetchall()


def create_notification(
    notification_type: str,
    message: str,
    title: str,
    user_id: Optional[int] = None,
    guardian_id: Optional[int] = None
) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO notifications (type, message, title, user_id, guardian_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (notification_type, message, title, user_id, guardian_id))
            notification_id = cur.fetchone()[0]
            conn.commit()
            return notification_id


def get_user_notifications(
    user_id: int,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            query = """
                SELECT id, type, message, user_id, guardian_id, created_at
                FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            if limit:
                query += f" LIMIT {limit}"
            
            cur.execute(query, (user_id,))
            return cur.fetchall()


def test_query():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            print(cur.fetchone())
