from datetime import datetime, timezone
from unittest.mock import patch

from tests.constants import REMINDER_DELAY_MINUTES, REMINDER_MAX_COUNT
from src.scheduler import Scheduler


@patch("src.scheduler.queue_email")
@patch("src.scheduler.create_notification")
@patch("src.scheduler.get_due_reminders")
def test_scheduler_queues_notifications_and_emails(
    mock_due,
    mock_create_notification,
    mock_queue_email,
):
    mock_due.return_value = [{
        "schedule_id": 10,
        "user_id": 1,
        "user_name": "Иван",
        "user_email": "patient@test.pi11box",
        "medication_name": "Аспирин",
        "dose": "100 мг",
        "intake_at": datetime.now(timezone.utc),
        "guardian_id": 2,
        "recipient_user_id": 2,
        "recipient_email": "guardian@test.pi11box",
        "sent_count": 0,
    }]

    with patch("src.scheduler.record_reminder_sent", return_value=1) as mock_record:
        results = Scheduler(
            grace_minutes=REMINDER_DELAY_MINUTES, max_reminders=REMINDER_MAX_COUNT
        ).process_missed_intakes()

    assert results[0]["status"] == "guardian"
    assert results[0]["attempt"] == 1
    mock_record.assert_called_once_with(10, 2)
    mock_create_notification.assert_called_once()
    mock_queue_email.assert_called_once()


@patch("src.scheduler.queue_email")
@patch("src.scheduler.create_notification")
@patch("src.scheduler.get_due_reminders")
def test_scheduler_notifies_patient(
    mock_due,
    mock_create_notification,
    mock_queue_email,
):
    mock_due.return_value = [{
        "schedule_id": 11,
        "user_id": 1,
        "user_name": "Иван",
        "user_email": "patient@test.pi11box",
        "medication_name": "Аспирин",
        "dose": None,
        "intake_at": datetime.now(timezone.utc),
        "guardian_id": None,
        "recipient_user_id": 1,
        "recipient_email": "patient@test.pi11box",
        "sent_count": 2,
    }]

    with patch("src.scheduler.record_reminder_sent", return_value=3) as mock_record:
        results = Scheduler(
            grace_minutes=REMINDER_DELAY_MINUTES, max_reminders=REMINDER_MAX_COUNT
        ).process_missed_intakes()

    assert results[0]["status"] == "patient"
    assert results[0]["attempt"] == 3
    mock_record.assert_called_once_with(11, 1)
    mock_create_notification.assert_called_once()
    mock_queue_email.assert_called_once()
    assert "3 из 3" in mock_create_notification.call_args[0][1]
