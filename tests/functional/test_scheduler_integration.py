from src.db import get_due_reminders, get_pending_emails
from src.scheduler import Scheduler
from tests.constants import REMINDER_DELAY_MINUTES, REMINDER_MAX_COUNT


def test_scheduler_creates_notifications_for_overdue_schedule(seeded):
    due = get_due_reminders(
        delay_minutes=REMINDER_DELAY_MINUTES, max_reminders=REMINDER_MAX_COUNT
    )
    assert len(due) >= 1

    results = Scheduler(
        grace_minutes=REMINDER_DELAY_MINUTES, max_reminders=REMINDER_MAX_COUNT
    ).process_missed_intakes()
    assert results
    assert any(r["status"] in {"guardian", "patient"} for r in results)

    due_after = get_due_reminders(
        delay_minutes=REMINDER_DELAY_MINUTES, max_reminders=REMINDER_MAX_COUNT
    )
    assert all(row["sent_count"] >= 1 for row in due_after)

    emails = get_pending_emails()
    assert len(emails) >= 1
