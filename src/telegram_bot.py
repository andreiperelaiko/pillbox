import json
import os
import time
from typing import Dict, List, Optional
from urllib import error, parse, request

from src.db import (
    get_guardian_invite,
    get_guardian_invites_to_notify,
    get_user_by_telegram,
    get_pending_notifications,
    invite_approver_party,
    mark_notification_sent,
    mark_guardian_invite_party_notified,
    respond_to_guardian_invite,
    save_telegram_chat_id,
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

    def _post_json(self, method: str, payload: Dict) -> Dict:
        req = request.Request(
            f"{self.base_url}/{method}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
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

    def send_message(
        self,
        chat_id: str,
        text: str,
        reply_markup: Optional[Dict] = None,
    ) -> Dict:
        payload: Dict = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self._post_json("sendMessage", payload)

    def answer_callback_query(self, callback_query_id: str, text: str) -> Dict:
        return self._post_json(
            "answerCallbackQuery",
            {"callback_query_id": callback_query_id, "text": text},
        )

    def get_updates(self, offset: Optional[int] = None, limit: int = 100) -> Dict:
        params: Dict = {"limit": limit}
        if offset is not None:
            params["offset"] = offset
        return self._api_call("getUpdates", params)

    def _invite_keyboard(self, invite_id: int) -> Dict:
        return {
            "inline_keyboard": [
                [
                    {"text": "Принять", "callback_data": f"gi:ok:{invite_id}"},
                    {"text": "Отклонить", "callback_data": f"gi:no:{invite_id}"},
                ]
            ]
        }

    def _notify_guardianship_completed(self, invite: Dict) -> None:
        patient_chat_id = invite.get("patient_chat_id")
        guardian_chat_id = invite.get("guardian_chat_id")
        patient_name = invite.get("patient_name") or "подопечный"
        guardian_name = invite.get("guardian_name") or "опекун"
        text = (
            f"Опекунство установлено: {guardian_name} следит за приёмами "
            f"пользователя {patient_name}."
        )
        if guardian_chat_id:
            self.send_message(str(guardian_chat_id), text)
        if patient_chat_id:
            self.send_message(str(patient_chat_id), text)

    def _notify_guardianship_rejected(self, invite: Dict, rejector_user_id: int) -> None:
        patient_chat_id = invite.get("patient_chat_id")
        guardian_chat_id = invite.get("guardian_chat_id")
        patient_name = invite.get("patient_name") or "подопечный"
        guardian_name = invite.get("guardian_name") or "опекун"

        if rejector_user_id == invite.get("guardian_user_id"):
            guardian_text = "Вы отклонили запрос на опекунство."
            patient_text = f"Опекун {guardian_name} отклонил запрос на опекунство."
        else:
            guardian_text = f"Подопечный {patient_name} отклонил запрос на опекунство."
            patient_text = "Вы отклонили запрос на опекунство."

        if guardian_chat_id:
            self.send_message(str(guardian_chat_id), guardian_text)
        if patient_chat_id:
            self.send_message(str(patient_chat_id), patient_text)

    def _handle_start(self, msg: Dict) -> Optional[Dict]:
        text = (msg.get("text") or "").strip()
        if not text.startswith("/start"):
            return None

        from_user = msg.get("from") or {}
        username = from_user.get("username")
        chat_id = str((msg.get("chat") or {}).get("id", ""))
        if not username or not chat_id:
            return None

        user = get_user_by_telegram(username)
        if not user:
            self.send_message(
                chat_id,
                f"Пользователь @{username} не найден. Сначала зарегистрируйтесь на сайте.",
            )
            return {"username": username, "chat_id": chat_id, "status": "not_found"}

        save_telegram_chat_id(user["id"], chat_id)
        self.send_message(
            chat_id,
            f"Привет, {user['name']}! Telegram привязан к {user['email']}.",
        )
        return {"username": username, "chat_id": chat_id, "user_id": user["id"], "status": "linked"}

    def _handle_callback(self, callback: Dict) -> Optional[Dict]:
        data = callback.get("data") or ""
        if not data.startswith("gi:"):
            return None

        parts = data.split(":")
        if len(parts) != 3:
            return None

        action, invite_id_str = parts[1], parts[2]
        try:
            invite_id = int(invite_id_str)
        except ValueError:
            return None

        from_user = callback.get("from") or {}
        username = from_user.get("username")
        if not username:
            return None

        user = get_user_by_telegram(username)
        if not user:
            return {"invite_id": invite_id, "status": "user_not_found"}

        callback_id = callback.get("id", "")
        approved = action == "ok"
        outcome = respond_to_guardian_invite(invite_id, user["id"], approved)
        invite = get_guardian_invite(invite_id)

        if outcome == "completed":
            self.answer_callback_query(callback_id, "Опекунство установлено.")
            if invite:
                self._notify_guardianship_completed(invite)
            return {"invite_id": invite_id, "status": "completed"}

        if outcome == "rejected":
            self.answer_callback_query(callback_id, "Запрос отклонён.")
            if invite:
                self._notify_guardianship_rejected(invite, user["id"])
            return {"invite_id": invite_id, "status": "rejected"}

        if outcome == "not_approver":
            self.answer_callback_query(
                callback_id,
                "Этот запрос подтверждает другой участник.",
            )
            return {"invite_id": invite_id, "status": "not_approver"}

        self.answer_callback_query(callback_id, "Не удалось обработать запрос.")
        return {"invite_id": invite_id, "status": "failed"}

    def process_updates(self) -> List[Dict]:
        updates = self.get_updates()
        if not updates.get("ok"):
            return []

        results = []
        max_update_id = None

        for item in updates.get("result", []):
            update_id = item.get("update_id", 0)
            if max_update_id is None or update_id > max_update_id:
                max_update_id = update_id

            if item.get("callback_query"):
                result = self._handle_callback(item["callback_query"])
                if result:
                    results.append({"type": "callback", **result})
                continue

            msg = item.get("message") or {}
            result = self._handle_start(msg)
            if result:
                results.append({"type": "start", **result})

        if max_update_id is not None:
            self.get_updates(offset=max_update_id + 1, limit=1)

        return results

    def process_guardian_invites(self) -> List[Dict]:
        results = []
        for invite in get_guardian_invites_to_notify():
            invite_id = invite["id"]
            patient_name = invite["patient_name"]
            guardian_name = invite.get("guardian_name") or "опекун"
            relationship = invite.get("relationship") or "опекун"
            initiated_by = invite.get("initiated_by") or "guardian"
            approver = invite_approver_party(initiated_by)
            keyboard = self._invite_keyboard(invite_id)

            guardian_chat_id = invite.get("guardian_chat_id")
            if guardian_chat_id and not invite.get("guardian_telegram_notified"):
                if initiated_by == "guardian":
                    text = (
                        f"Вы отправили запрос на опекунство пользователя {patient_name} "
                        f"(роль: {relationship}).\n\n"
                        "Ожидаем подтверждения подопечного в Telegram."
                    )
                    reply_markup = None
                else:
                    text = (
                        f"Пользователь {patient_name} приглашает вас стать опекуном "
                        f"(роль: {relationship}).\n\n"
                        "Подтвердите или отклоните запрос:"
                    )
                    reply_markup = keyboard if approver == "guardian" else None
                res = self.send_message(
                    str(guardian_chat_id), text, reply_markup=reply_markup
                )
                if res.get("ok"):
                    mark_guardian_invite_party_notified(invite_id, "guardian")
                    results.append(
                        {"invite_id": invite_id, "party": "guardian", "status": "sent"}
                    )
                else:
                    results.append(
                        {
                            "invite_id": invite_id,
                            "party": "guardian",
                            "status": "failed",
                            "reason": res.get("description"),
                        }
                    )

            patient_chat_id = invite.get("patient_chat_id")
            if patient_chat_id and not invite.get("patient_telegram_notified"):
                if initiated_by == "patient":
                    text = (
                        f"Вы пригласили {guardian_name} стать опекуном "
                        f"(роль: {relationship}).\n\n"
                        "Ожидаем подтверждения опекуна в Telegram."
                    )
                    reply_markup = None
                else:
                    text = (
                        f"Опекун {guardian_name} хочет следить за вашими приёмами "
                        f"(роль: {relationship}).\n\n"
                        "Подтвердите или отклоните запрос:"
                    )
                    reply_markup = keyboard if approver == "patient" else None
                res = self.send_message(
                    str(patient_chat_id), text, reply_markup=reply_markup
                )
                if res.get("ok"):
                    mark_guardian_invite_party_notified(invite_id, "patient")
                    results.append(
                        {"invite_id": invite_id, "party": "patient", "status": "sent"}
                    )
                else:
                    results.append(
                        {
                            "invite_id": invite_id,
                            "party": "patient",
                            "status": "failed",
                            "reason": res.get("description"),
                        }
                    )

        return results

    def process_notifications(self) -> List[Dict]:
        pending = get_pending_notifications()
        results = []

        for n in pending:
            chat_id = n.get("telegram_chat_id")
            if not chat_id:
                continue
            res = self.send_message(str(chat_id), n["text"])
            if res.get("ok"):
                mark_notification_sent(n["id"])
                results.append({"notification_id": n["id"], "status": "sent"})
            else:
                results.append({"notification_id": n["id"], "status": "failed", "reason": res.get("description")})

        return results

    def run(self, interval: int = 10) -> None:
        print(f"Бот запущен, интервал опроса: {interval}с")
        while True:
            try:
                for result in self.process_updates():
                    print(f"  [update] {result}")

                for result in self.process_guardian_invites():
                    print(f"  [invite] {result}")

                for result in self.process_notifications():
                    print(f"  [notify] {result}")
            except Exception as exc:
                print(f"  [error] {exc}")

            time.sleep(interval)
