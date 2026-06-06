import os
from typing import Dict, List

from src.db import (
    create_notification,
    get_due_reminders,
    queue_email,
    record_reminder_sent,
)
from src.time_format import format_intake_datetime


class Scheduler:
    def __init__(
        self,
        grace_minutes: int | None = None,
        max_reminders: int | None = None,
    ):
        self.delay_minutes = int(
            grace_minutes
            if grace_minutes is not None
            else os.getenv("SCHEDULER_GRACE_MINUTES", "1")
        )
        self.max_reminders = int(
            max_reminders
            if max_reminders is not None
            else os.getenv("SCHEDULER_MAX_REMINDERS", "3")
        )

    def process_missed_intakes(self) -> List[Dict]:
        results = []
        due = get_due_reminders(
            delay_minutes=self.delay_minutes,
            max_reminders=self.max_reminders,
        )

        for item in due:
            schedule_id = item["schedule_id"]
            user_name = item["user_name"]
            medication_name = item["medication_name"]
            dose = item.get("dose") or "не указана"
            intake_at = item["intake_at"]
            guardian_id = item.get("guardian_id")
            recipient_email = item.get("recipient_email")
            attempt = int(item.get("sent_count") or 0) + 1
            intake_local = format_intake_datetime(intake_at)

            text = (
                f"Напоминание {attempt} из {self.max_reminders}: пропущен приём "
                f"{medication_name} ({dose}) для {user_name} в {intake_local}."
            )

            recipient_user_id = int(item["recipient_user_id"])
            sent_count = record_reminder_sent(schedule_id, recipient_user_id)

            create_notification(schedule_id, text, guardian_id)
            if recipient_email:
                subject = (
                    "Pillbox: пропущен приём лекарства"
                    if guardian_id
                    else "Pillbox: напоминание о приёме"
                )
                queue_email(recipient_email, subject, text)

            results.append(
                {
                    "schedule_id": schedule_id,
                    "guardian_id": guardian_id,
                    "recipient_user_id": recipient_user_id,
                    "attempt": sent_count,
                    "status": "guardian" if guardian_id else "patient",
                }
            )

        return results

    def run(self, interval: int = 60) -> None:
        import time

        print(
            f"Scheduler запущен, интервал {interval}с, "
            f"задержка {self.delay_minutes} мин, макс. {self.max_reminders} напоминаний"
        )
        while True:
            try:
                for result in self.process_missed_intakes():
                    print(f"  [schedule] {result}")
            except Exception as exc:
                print(f"  [error] {exc}")
            time.sleep(interval)
