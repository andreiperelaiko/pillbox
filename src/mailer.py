import os
import smtplib
from email.message import EmailMessage
from typing import Dict, List, Optional

from src.db import get_pending_emails, mark_email_sent


class Mailer:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        from_addr: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: Optional[bool] = None,
    ):
        self.host = host or os.getenv("SMTP_HOST", "mailpit")
        self.port = int(port or os.getenv("SMTP_PORT", "1025"))
        self.from_addr = from_addr or os.getenv("SMTP_FROM", "noreply@pi11box.ru")
        self.username = username or os.getenv("SMTP_USER")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.use_tls = use_tls if use_tls is not None else os.getenv("SMTP_USE_TLS", "false").lower() == "true"

    def send(self, to_email: str, subject: str, body: str) -> Dict:
        message = EmailMessage()
        message["From"] = self.from_addr
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as smtp:
                if self.use_tls:
                    smtp.starttls()
                if self.username and self.password:
                    smtp.login(self.username, self.password)
                smtp.send_message(message)
            return {"status": "sent", "to": to_email}
        except Exception as exc:
            return {"status": "failed", "to": to_email, "reason": str(exc)}

    def process_outbox(self) -> List[Dict]:
        results = []
        for item in get_pending_emails():
            result = self.send(item["to_email"], item["subject"], item["body"])
            if result["status"] == "sent":
                mark_email_sent(item["id"])
            results.append({"email_id": item["id"], **result})
        return results

    def run(self, interval: int = 15) -> None:
        import time

        print(f"Mailer запущен, SMTP {self.host}:{self.port}, интервал {interval}с")
        while True:
            try:
                for result in self.process_outbox():
                    print(f"  [mail] {result}")
            except Exception as exc:
                print(f"  [error] {exc}")
            time.sleep(interval)
