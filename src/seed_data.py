from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from src.auth import hash_password
from src.db import (
    add_guardian,
    create_medication,
    create_schedule,
    create_user_with_password,
    ensure_schedule_notification_schema,
    get_auth_user_by_email,
    get_conn,
)


def reset_test_data() -> None:
    ensure_schedule_notification_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                TRUNCATE TABLE
                  email_outbox,
                  notifications,
                  sessions,
                  medication_schedules,
                  user_guardians,
                  medications,
                  users
                RESTART IDENTITY CASCADE
            """)
            conn.commit()


def _ensure_guardian_link(user_id: int, guardian_id: int) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM user_guardians
                WHERE user_id = %s AND guardian_id = %s
                """,
                (user_id, guardian_id),
            )
            if cur.fetchone():
                return
    add_guardian(user_id, guardian_id, "дочь")


def seed_demo_data() -> Dict[str, int]:
    ensure_schedule_notification_schema()

    user = get_auth_user_by_email("patient@test.pi11box")
    user_id = user["id"] if user else create_user_with_password(
        "patient@test.pi11box",
        "Тестовый пациент",
        hash_password("testpass123"),
        phone="+79001112233",
        telegram="test_patient",
    )

    guardian = get_auth_user_by_email("guardian@test.pi11box")
    guardian_id = guardian["id"] if guardian else create_user_with_password(
        "guardian@test.pi11box",
        "Тестовый опекун",
        hash_password("testpass123"),
        telegram="test_guardian",
    )

    _ensure_guardian_link(user_id, guardian_id)

    med_id = create_medication("Аспирин", "Тестовый препарат", user_id=user_id)
    overdue_at = datetime.now(timezone.utc) - timedelta(minutes=3)
    upcoming_at = datetime.now(timezone.utc) + timedelta(hours=2)

    overdue_id = create_schedule(med_id, overdue_at, "100 мг", user_id=user_id)
    create_schedule(med_id, upcoming_at, "100 мг", user_id=user_id)

    return {
        "user_id": user_id,
        "guardian_id": guardian_id,
        "medication_id": med_id,
        "overdue_schedule_id": overdue_id,
    }


def seed_if_empty() -> Optional[Dict[str, int]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM medication_schedules")
            schedule_count = cur.fetchone()[0]
    if user_count > 0 and schedule_count > 0:
        return None
    return seed_demo_data()
