from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from tests.constants import REMINDER_DELAY_MINUTES, REMINDER_MAX_COUNT
from src.auth import hash_password
from src.db import (
    create_medication,
    create_notification,
    create_schedule,
    create_user_with_password,
    get_conn,
    get_due_reminders,
    get_reminder_sent_count,
    record_reminder_sent,
)
from src.scheduler import Scheduler


def _age_last_sent(schedule_id: int, recipient_user_id: int, minutes: int) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE schedule_reminder_stats
                SET last_sent_at = CURRENT_TIMESTAMP - (%s * INTERVAL '1 minute')
                WHERE schedule_id = %s AND recipient_user_id = %s
                """,
                (minutes, schedule_id, recipient_user_id),
            )
            conn.commit()


def test_reminder_count_stored_in_db(client):
    user_id = create_user_with_password(
        "reminder_count@test.pi11box",
        "Пациент",
        hash_password("secret123"),
        telegram="patient_rc",
    )
    med_id = create_medication("Тест", user_id=user_id)
    intake_at = datetime.now(timezone.utc) - timedelta(minutes=2)
    schedule_id = create_schedule(med_id, intake_at, "1 таб", user_id=user_id)

    assert get_reminder_sent_count(schedule_id, user_id) == 0

    due_before = get_due_reminders(
        delay_minutes=REMINDER_DELAY_MINUTES, max_reminders=REMINDER_MAX_COUNT
    )
    assert any(
        row["schedule_id"] == schedule_id and row["sent_count"] == 0
        for row in due_before
    )

    assert record_reminder_sent(schedule_id, user_id) == 1
    assert get_reminder_sent_count(schedule_id, user_id) == 1
    assert record_reminder_sent(schedule_id, user_id) == 2

    due_after = get_due_reminders(
        delay_minutes=REMINDER_DELAY_MINUTES, max_reminders=REMINDER_MAX_COUNT
    )
    patient_rows = [
        row for row in due_after
        if row["schedule_id"] == schedule_id and row["guardian_id"] is None
    ]
    if patient_rows:
        assert patient_rows[0]["sent_count"] == 2
    else:
        assert get_reminder_sent_count(schedule_id, user_id) == 2


def test_scheduler_cycle_increments_count_by_one(client):
    user_id = create_user_with_password(
        "reminder_cycle@test.pi11box",
        "Пациент",
        hash_password("secret123"),
        telegram="patient_cycle",
    )
    med_id = create_medication("Тест", user_id=user_id)
    intake_at = datetime.now(timezone.utc) - timedelta(minutes=2)
    schedule_id = create_schedule(med_id, intake_at, "1 таб", user_id=user_id)

    with patch("src.scheduler.queue_email"), patch("src.scheduler.create_notification"):
        Scheduler(
            grace_minutes=REMINDER_DELAY_MINUTES, max_reminders=REMINDER_MAX_COUNT
        ).process_missed_intakes()

    assert get_reminder_sent_count(schedule_id, user_id) == 1

    create_notification(schedule_id, "тест", None)
    assert get_reminder_sent_count(schedule_id, user_id) == 1


def test_scheduler_sends_sequential_attempt_numbers(client):
    user_id = create_user_with_password(
        "reminder_seq@test.pi11box",
        "Пациент",
        hash_password("secret123"),
        telegram="patient_seq",
    )
    med_id = create_medication("Тест", user_id=user_id)
    intake_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    schedule_id = create_schedule(med_id, intake_at, "1 таб", user_id=user_id)

    attempts = []
    scheduler = Scheduler(
        grace_minutes=REMINDER_DELAY_MINUTES, max_reminders=REMINDER_MAX_COUNT
    )
    with patch("src.scheduler.queue_email"), patch("src.scheduler.create_notification"):
        for _ in range(3):
            results = scheduler.process_missed_intakes()
            if results:
                attempts.append(results[0]["attempt"])
            _age_last_sent(schedule_id, user_id, minutes=2)

    assert attempts == [1, 2, 3]
    assert get_reminder_sent_count(schedule_id, user_id) == 3
