import json
import os
import time
from typing import Dict, List, Optional
from urllib import error, parse, request

from src.db import (
    get_user, get_user_by_telegram, get_user_guardians,
    save_telegram_chat_id, create_notification,
    get_pending_notifications, delete_notification,
)


class TelegramBot:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def _api_call(self, method: str, params: Optional[Dict] = None) -> Dict:
        url = f"{self.base_url}/{method}"
        if params:
            url += "?" + parse.urlencode(params)
        req = request.Request(url, method="GET")
        try:
            with request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            data = exc.read().decode("utf-8")
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return {"ok": False, "description": data}
        except Exception as exc:
            return {"ok": False, "description": str(exc)}

    def send_message(self, chat_id: str, text: str) -> Dict:
        payload = parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
        req = request.Request(f"{self.base_url}/sendMessage", data=payload, method="POST")
        try:
            with request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            data = exc.read().decode("utf-8")
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return {"ok": False, "description": data}
        except Exception as exc:
            return {"ok": False, "description": str(exc)}

    def get_updates(self, offset: Optional[int] = None, limit: int = 100) -> Dict:
        params: Dict = {"limit": limit}
        if offset is not None:
            params["offset"] = offset
        return self._api_call("getUpdates", params)

    def process_updates(self) -> List[Dict]:
        """Обрабатывает /start: находит пользователя по @username и сохраняет chat_id."""
        updates = self.get_updates()
        if not updates.get("ok"):
            return []

        results = []
        max_update_id = None

        for item in updates.get("result", []):
            update_id = item.get("update_id", 0)
            if max_update_id is None or update_id > max_update_id:
                max_update_id = update_id

            msg = item.get("message") or {}
            text = (msg.get("text") or "").strip()
            if text != "/start":
                continue

            from_user = msg.get("from") or {}
            username = from_user.get("username")
            chat_id = str((msg.get("chat") or {}).get("id", ""))

            if not username or not chat_id:
                continue

            user = get_user_by_telegram(username)
            if not user:
                self.send_message(chat_id, f"Пользователь @{username} не найден. Сначала зарегистрируйтесь.")
                results.append({"username": username, "chat_id": chat_id, "status": "not_found"})
                continue

            save_telegram_chat_id(user["id"], chat_id)
            self.send_message(chat_id, f"Привет, {user['name']}! Telegram привязан к {user['email']}.")
            results.append({"username": username, "chat_id": chat_id, "user_id": user["id"], "status": "linked"})

        if max_update_id is not None:
            self.get_updates(offset=max_update_id + 1, limit=1)

        return results

    def process_notifications(self) -> List[Dict]:
        """Берёт все notifications из БД, отправляет в Telegram, удаляет отправленные."""
        pending = get_pending_notifications()
        results = []

        for n in pending:
            chat_id = n.get("telegram_chat_id")
            if not chat_id:
                continue
            res = self.send_message(str(chat_id), n["text"])
            if res.get("ok"):
                delete_notification(n["id"])
                results.append({"notification_id": n["id"], "status": "sent"})
            else:
                results.append({"notification_id": n["id"], "status": "failed", "reason": res.get("description")})

        return results

    def run(self, interval: int = 10) -> None:
        """Основной цикл: обрабатывает /start и отправляет уведомления каждые interval секунд."""
        print(f"Бот запущен, интервал опроса: {interval}с")
        while True:
            try:
                linked = self.process_updates()
                for r in linked:
                    print(f"  [start] {r}")

                sent = self.process_notifications()
                for r in sent:
                    print(f"  [notify] {r}")
            except Exception as e:
                print(f"  [error] {e}")

            time.sleep(interval)
