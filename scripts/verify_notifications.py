#!/usr/bin/env python3
"""Однократная проверка цепочки уведомлений: scheduler → email_outbox/mailer → Telegram."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def mailpit_message_count() -> int | None:
    host = os.getenv("MAILPIT_API_HOST", "127.0.0.1")
    port = os.getenv("MAILPIT_API_PORT", "8025")
    url = f"http://{host}:{port}/api/v1/messages"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return int(data.get("total", 0))
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


def main() -> int:
    from src.db import get_conn, get_pending_emails, get_pending_notifications
    from src.mailer import Mailer
    from src.scheduler import Scheduler
    from src.telegram_bot import TelegramBot

    print("=== Pillbox: проверка уведомлений ===\n")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM medication_schedules WHERE taken = FALSE AND intake_at < NOW()")
            overdue_before = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE telegram_chat_id IS NOT NULL")
            linked_tg = cur.fetchone()[0]

    print(f"Просроченных приёмов (ещё без уведомления — см. scheduler): {overdue_before}")
    print(f"Пользователей с привязанным Telegram: {linked_tg}")
    print(f"SMTP: {os.getenv('SMTP_HOST', 'mailpit')}:{os.getenv('SMTP_PORT', '1025')}")
    print()

    mailpit_before = mailpit_message_count()
    if mailpit_before is not None:
        print(f"Mailpit: писем до проверки — {mailpit_before}")
    else:
        print("Mailpit API недоступен (http://127.0.0.1:8025) — письма не проверить в UI")

    print("\n1) Scheduler...")
    scheduler_results = Scheduler().process_missed_intakes()
    print(f"   обработано: {len(scheduler_results)}")
    for item in scheduler_results[:5]:
        print(f"   - {item}")
    if len(scheduler_results) > 5:
        print(f"   ... и ещё {len(scheduler_results) - 5}")

    pending_emails = len(get_pending_emails())
    pending_tg = len(get_pending_notifications())
    print(f"\n   в очереди email: {pending_emails}, TG (с chat_id): {pending_tg}")

    print("\n2) Mailer...")
    mailer_results = Mailer().process_outbox()
    sent = sum(1 for r in mailer_results if r.get("status") == "sent")
    failed = sum(1 for r in mailer_results if r.get("status") == "failed")
    print(f"   отправлено: {sent}, ошибок: {failed}")
    for item in mailer_results[:3]:
        print(f"   - {item}")
    if len(mailer_results) > 3:
        print(f"   ... и ещё {len(mailer_results) - 3}")

    print("\n3) Telegram bot...")
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        print("   TELEGRAM_BOT_TOKEN не задан — пропуск")
        tg_results = []
    else:
        bot = TelegramBot()
        me = bot._api_call("getMe")
        if me.get("ok"):
            print(f"   бот: @{me['result'].get('username')}")
        tg_results = bot.process_notifications()
        tg_sent = sum(1 for r in tg_results if r.get("status") == "sent")
        tg_failed = sum(1 for r in tg_results if r.get("status") == "failed")
        print(f"   отправлено: {tg_sent}, ошибок: {tg_failed}")
        for item in tg_results[:3]:
            print(f"   - {item}")

    mailpit_after = mailpit_message_count()
    if mailpit_before is not None and mailpit_after is not None:
        print(f"\nMailpit: писем после проверки — {mailpit_after} (+{mailpit_after - mailpit_before})")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM email_outbox WHERE sent_at IS NULL")
            unsent = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM notifications")
            notifications_left = cur.fetchone()[0]

    print(f"\nИтог: неотправленных писем в БД — {unsent}, записей notifications — {notifications_left}")

    if linked_tg == 0:
        print(
            "\n⚠ Telegram: ни у кого нет chat_id. Напишите боту /start "
            "(username в .env TELEGRAM — см. @p111boxbot), telegram в профиле должен совпадать."
        )

    if mailpit_before is None and not mailer_results:
        print("\n⚠ Email: настройте SMTP в .env или запустите Mailpit (docker).")

    ok = (sent > 0 or len(scheduler_results) == 0) and (linked_tg == 0 or any(r.get("status") == "sent" for r in tg_results) or pending_tg == 0)
    return 0 if sent > 0 or len(scheduler_results) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
