import os

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.db import (
    get_user, get_user_by_email,
    create_medication, get_medications, get_medication, delete_medication,
    create_schedule, get_medication_schedules, log_medication_taken, delete_schedule,
    add_guardian, get_user_guardians, get_user_wards, remove_guardian_link, guardian_link_exists,
    create_guardian_invite,
    create_notification, get_user_notifications,
    create_user_with_password, get_auth_user_by_email,
    create_session, delete_session, delete_user_sessions,
    create_email_verification_token, verify_email_by_token, update_user_telegram,
    normalize_telegram_username, telegram_username_taken,
    queue_email,
)
from src.auth import (
    SESSION_COOKIE_NAME, clear_session_cookie, create_session_id,
    get_current_user, get_session_expiry, hash_password,
    set_session_cookie, verify_password,
)
app = FastAPI(
    title="Pillbox API",
    version="1.0.0",
    root_path="/api",
    description="API для управления приёмом лекарств, расписаниями и уведомлениями. "
                "Все эндпоинты кроме /auth/register и /auth/login требуют cookie-сессию. "
                "Сначала вызовите /auth/login — cookie установится автоматически.",
)

Auth = Depends(get_current_user)

APP_PUBLIC_URL = os.getenv("APP_PUBLIC_URL", "https://pi11box.ru").rstrip("/")
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "p111boxbot").lstrip("@")


def _telegram_bot_url() -> str:
    return f"https://t.me/{TELEGRAM_BOT_USERNAME}?start=link"


def _require_telegram_linked(user: dict, role: str) -> None:
    if not user.get("telegram_chat_id"):
        raise HTTPException(
            400,
            f"{role} must link and verify Telegram in settings before guardian invites",
        )


def _create_guardian_invite_flow(
    patient_user_id: int,
    guardian_user_id: int,
    relationship: Optional[str],
    initiated_by: str,
) -> GuardianInviteResponse:
    if patient_user_id == guardian_user_id:
        raise HTTPException(400, "Cannot be guardian of yourself")
    patient = get_user(patient_user_id)
    guardian = get_user(guardian_user_id)
    if not patient or not guardian:
        raise HTTPException(404, "User not found")
    if guardian_link_exists(patient_user_id, guardian_user_id):
        raise HTTPException(400, "You are already a guardian for this user")
    if initiated_by == "guardian":
        _require_telegram_linked(patient, "Patient")
        message = (
            "Запрос отправлен. Подопечный должен подтвердить его в Telegram (@p111boxbot)."
        )
    else:
        _require_telegram_linked(guardian, "Guardian")
        message = (
            "Приглашение отправлено. Опекун должен подтвердить его в Telegram (@p111boxbot)."
        )
    invite_id = create_guardian_invite(
        patient_user_id, guardian_user_id, relationship, initiated_by=initiated_by
    )
    return GuardianInviteResponse(
        id=invite_id,
        status="pending",
        message=message,
    )


def _public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "phone": user.get("phone"),
        "telegram": user.get("telegram"),
        "telegram_chat_id": user.get("telegram_chat_id"),
        "email_verified": bool(user.get("email_verified")),
        "telegram_verified": bool(user.get("telegram_chat_id")),
    }


# ──── Models ────

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    phone: Optional[str]
    telegram: Optional[str]
    telegram_chat_id: Optional[str]
    email_verified: bool = False
    telegram_verified: bool = False

class AccountSettingsResponse(BaseModel):
    email: str
    email_verified: bool
    telegram: Optional[str]
    telegram_verified: bool
    telegram_bot_url: str
    site_settings_url: str

class MessageResponse(BaseModel):
    message: str

class ProfileUpdateRequest(BaseModel):
    telegram: Optional[str] = None

class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    phone: Optional[str] = None
    telegram: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False

class LoginResponse(BaseModel):
    message: str

class LogoutAllResponse(BaseModel):
    message: str
    sessions_revoked: int

class MedicationCreate(BaseModel):
    name: str
    description: Optional[str] = None

class MedicationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

class ScheduleCreate(BaseModel):
    intake_at: datetime
    dose: Optional[str] = None

class ScheduleResponse(BaseModel):
    id: int
    medication_id: int
    intake_at: datetime
    taken: bool
    dose: Optional[str]

class MarkScheduleRequest(BaseModel):
    schedule_id: int

class GuardianAdd(BaseModel):
    guardian_id: int
    relationship: Optional[str] = None

class GuardianAttachRequest(BaseModel):
    relationship: Optional[str] = None

class GuardianPersonResponse(BaseModel):
    id: int
    email: str
    name: str
    relationship: Optional[str] = None

class GuardianInviteResponse(BaseModel):
    id: int
    status: str
    message: str

class GuardianInviteByEmailRequest(BaseModel):
    email: str
    relationship: Optional[str] = None

class NotificationCreate(BaseModel):
    schedule_id: int
    text: str
    guardian_id: Optional[int] = None

class NotificationResponse(BaseModel):
    id: int
    schedule_id: int
    guardian_id: Optional[int]
    text: str


# ──── Auth ────

@app.get("/", tags=["health"])
def root():
    return {"message": "Pillbox API", "version": "1.0.0"}


@app.post("/auth/register", response_model=UserResponse, status_code=201, tags=["auth"],
          summary="Регистрация нового пользователя",
          description="Создаёт аккаунт по email + пароль. "
                      "Опционально можно указать telegram (@username) — "
                      "при отправке /start боту chat_id привяжется автоматически. "
                      "После регистрации нужно вызвать /auth/login для получения сессии.")
def register_endpoint(p: RegisterRequest):
    if get_auth_user_by_email(p.email):
        raise HTTPException(400, "Email already exists")
    if p.telegram:
        normalized = normalize_telegram_username(p.telegram)
        if normalized and telegram_username_taken(normalized):
            raise HTTPException(400, "Telegram username already in use")
    uid = create_user_with_password(
        p.email, p.name, hash_password(p.password), p.phone, p.telegram
    )
    user = get_user(uid)
    if not user:
        raise HTTPException(404, "User not found after creation")
    return _public_user(user)


@app.post("/auth/login", response_model=LoginResponse, tags=["auth"],
          summary="Войти и получить cookie-сессию",
          description="Проверяет email + пароль. При успехе ставит HttpOnly cookie `pillbox_session`. "
                      "Если `remember_me=true` — сессия живёт 30 дней, иначе 1 день. "
                      "Cookie автоматически отправляется со всеми последующими запросами.")
def login_endpoint(p: LoginRequest, response: Response):
    user = get_auth_user_by_email(p.email)
    if not user or not verify_password(p.password, user.get("password_hash", "")):
        raise HTTPException(401, "Invalid credentials")
    sid = create_session_id()
    create_session(sid, user["id"], get_session_expiry(p.remember_me))
    set_session_cookie(response, sid, p.remember_me)
    return {"message": "Logged in"}


@app.get("/auth/me", response_model=UserResponse, tags=["auth"],
         summary="Текущий пользователь",
         description="Возвращает данные пользователя по текущей cookie-сессии. "
                     "Сессия проверяется в БД на каждый запрос (актуальность + срок действия).")
def me_endpoint(me: dict = Auth):
    return _public_user(me)


@app.get("/auth/settings", response_model=AccountSettingsResponse, tags=["auth"],
         summary="Настройки верификации",
         description="Статус подтверждения email и Telegram, ссылки для верификации.")
def settings_endpoint(me: dict = Auth):
    user = get_user(me["id"])
    if not user:
        raise HTTPException(404, "User not found")
    public = _public_user(user)
    return {
        "email": public["email"],
        "email_verified": public["email_verified"],
        "telegram": public.get("telegram"),
        "telegram_verified": public["telegram_verified"],
        "telegram_bot_url": _telegram_bot_url(),
        "site_settings_url": f"{APP_PUBLIC_URL}/site/settings",
    }


@app.post("/auth/verification/email/send", response_model=MessageResponse, tags=["auth"],
          summary="Отправить письмо для подтверждения email",
          description="Ставит письмо в очередь с ссылкой подтверждения (действует 24 часа).")
def send_email_verification_endpoint(me: dict = Auth):
    user = get_user(me["id"])
    if not user:
        raise HTTPException(404, "User not found")
    if user.get("email_verified"):
        return {"message": "Email already verified"}

    token = create_email_verification_token(user["id"])
    verify_url = f"{APP_PUBLIC_URL}/api/auth/verification/email/confirm?token={token}"
    body = (
        f"Здравствуйте, {user['name']}!\n\n"
        f"Подтвердите email для Pillbox:\n{verify_url}\n\n"
        f"Ссылка действует 24 часа."
    )
    queue_email(user["email"], "Pillbox: подтверждение email", body)
    return {"message": "Verification email queued"}


@app.get("/auth/verification/email/confirm", tags=["auth"],
         summary="Подтвердить email по ссылке из письма",
         description="Публичный редирект: подтверждает email и возвращает на /site/settings.")
def confirm_email_endpoint(token: str):
    user_id = verify_email_by_token(token)
    settings_url = f"{APP_PUBLIC_URL}/site/settings"
    if not user_id:
        return RedirectResponse(
            url=f"{settings_url}?email_verified=0&reason=invalid_or_expired",
            status_code=302,
        )
    return RedirectResponse(url=f"{settings_url}?email_verified=1", status_code=302)


@app.patch("/auth/profile", response_model=UserResponse, tags=["auth"],
           summary="Обновить профиль",
           description="Сейчас можно указать Telegram @username. При смене username привязка сбрасывается.")
def update_profile_endpoint(body: ProfileUpdateRequest, me: dict = Auth):
    if body.telegram is not None:
        normalized = normalize_telegram_username(body.telegram)
        if normalized and (len(normalized) < 5 or len(normalized) > 32):
            raise HTTPException(400, "Invalid telegram username")
        if normalized and telegram_username_taken(normalized, exclude_user_id=me["id"]):
            raise HTTPException(400, "Telegram username already in use")
        if not update_user_telegram(me["id"], normalized):
            raise HTTPException(404, "User not found")
    user = get_user(me["id"])
    if not user:
        raise HTTPException(404, "User not found")
    return _public_user(user)


@app.post("/auth/logout", response_model=LoginResponse, tags=["auth"],
          summary="Выйти из текущей сессии",
          description="Удаляет текущую сессию из БД и очищает cookie. "
                      "Другие сессии (другие устройства) остаются активными.")
def logout_endpoint(request: Request, response: Response, _: dict = Auth):
    sid = request.cookies.get(SESSION_COOKIE_NAME)
    if sid:
        delete_session(sid)
    clear_session_cookie(response)
    return {"message": "Logged out"}


@app.post("/auth/logout-all", response_model=LogoutAllResponse, tags=["auth"],
          summary="Выйти со всех устройств",
          description="Удаляет все сессии пользователя из БД. "
                      "После этого ни одно устройство не сможет делать запросы без повторного логина.")
def logout_all_endpoint(response: Response, me: dict = Auth):
    deleted = delete_user_sessions(me["id"])
    clear_session_cookie(response)
    return {"message": "Logged out from all devices", "sessions_revoked": deleted}


# ──── Users ────


@app.get("/users/{user_id}", response_model=UserResponse, tags=["users"],
         summary="Получить пользователя по ID",
         description="Возвращает данные пользователя: email, имя, телефон, telegram, привязанный chat_id.")
def get_user_endpoint(user_id: int, _: dict = Auth):
    user = get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return _public_user(user)


@app.get("/users/email/{email}", response_model=UserResponse, tags=["users"],
         summary="Найти пользователя по email",
         description="Поиск пользователя по точному совпадению email. Возвращает 404 если не найден.")
def get_user_by_email_endpoint(email: str, _: dict = Auth):
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(404, "User not found")
    return _public_user(user)


# ──── Medications ────

@app.post("/medications", response_model=MedicationResponse, status_code=201, tags=["medications"],
          summary="Создать препарат",
          description="Добавляет новый препарат в справочник. "
                      "Содержит только название и описание. Дозировка указывается при создании расписания.")
def create_medication_endpoint(m: MedicationCreate, me: dict = Auth):
    mid = create_medication(m.name, m.description, user_id=me["id"])
    med = get_medication(mid, user_id=me["id"])
    if not med:
        raise HTTPException(404, "Medication not found after creation")
    return med


@app.get("/medications", response_model=List[MedicationResponse], tags=["medications"],
         summary="Список препаратов текущего пользователя",
         description="Возвращает только препараты, созданные текущим пользователем.")
def get_medications_endpoint(me: dict = Auth):
    return get_medications(me["id"])


@app.get("/medications/{medication_id}", response_model=MedicationResponse, tags=["medications"],
         summary="Получить препарат по ID",
         description="Возвращает препарат только если он принадлежит текущему пользователю.")
def get_medication_endpoint(medication_id: int, me: dict = Auth):
    med = get_medication(medication_id, user_id=me["id"])
    if not med:
        raise HTTPException(404, "Medication not found")
    return med


@app.delete("/medications/{medication_id}", status_code=204, tags=["medications"],
            summary="Удалить препарат",
            description="Удаляет препарат текущего пользователя и все связанные приёмы.")
def delete_medication_endpoint(medication_id: int, me: dict = Auth):
    if not delete_medication(medication_id, user_id=me["id"]):
        raise HTTPException(404, "Medication not found")
    return Response(status_code=204)


# ──── Schedules ────

@app.post("/medications/{medication_id}/schedules", response_model=ScheduleResponse, status_code=201,
          tags=["schedules"],
          summary="Создать запись в расписании",
          description="Добавляет приём: когда принять (intake_at) и в какой дозе (dose). "
                      "Поле taken по умолчанию false — означает что приём ещё не выполнен.")
def create_schedule_endpoint(medication_id: int, s: ScheduleCreate, me: dict = Auth):
    if not get_medication(medication_id, user_id=me["id"]):
        raise HTTPException(404, "Medication not found")
    sid = create_schedule(medication_id, s.intake_at, s.dose, user_id=me["id"])
    entry = next(
        (x for x in get_medication_schedules(medication_id, user_id=me["id"]) if x["id"] == sid),
        None,
    )
    if not entry:
        raise HTTPException(404, "Schedule not found after creation")
    return entry


@app.get("/medications/{medication_id}/schedules", response_model=List[ScheduleResponse],
         tags=["schedules"],
         summary="Расписание препарата",
         description="Приёмы, назначенные текущим пользователем для данного препарата.")
def get_medication_schedules_endpoint(medication_id: int, me: dict = Auth):
    if not get_medication(medication_id, user_id=me["id"]):
        raise HTTPException(404, "Medication not found")
    return get_medication_schedules(medication_id, user_id=me["id"])


@app.post("/medications/{medication_id}/schedules/mark-taken", response_model=ScheduleResponse,
          tags=["schedules"],
          summary="Отметить приём",
          description="Ставит taken=true для указанного schedule_id. "
                      "Если приём не отмечен — считается пропущенным.")
def mark_taken_endpoint(medication_id: int, body: MarkScheduleRequest, me: dict = Auth):
    if not get_medication(medication_id, user_id=me["id"]):
        raise HTTPException(404, "Medication not found")
    uid = log_medication_taken(body.schedule_id, user_id=me["id"])
    if not uid:
        raise HTTPException(404, "Schedule not found")
    entry = next(
        (x for x in get_medication_schedules(medication_id, user_id=me["id"]) if x["id"] == uid),
        None,
    )
    if not entry:
        raise HTTPException(404, "Schedule not found after update")
    return entry


@app.delete("/medications/{medication_id}/schedules/{schedule_id}", status_code=204,
            tags=["schedules"],
            summary="Удалить приём из расписания",
            description="Удаляет запись расписания, если она принадлежит текущему пользователю.")
def delete_schedule_endpoint(medication_id: int, schedule_id: int, me: dict = Auth):
    if not get_medication(medication_id, user_id=me["id"]):
        raise HTTPException(404, "Medication not found")
    if not delete_schedule(schedule_id, user_id=me["id"], medication_id=medication_id):
        raise HTTPException(404, "Schedule not found")
    return Response(status_code=204)


# ──── Guardians ────

@app.get("/guardians", response_model=List[GuardianPersonResponse], tags=["guardians"],
         summary="Мои опекуны",
         description="Пользователи, которые следят за моими приёмами.")
def my_guardians_endpoint(me: dict = Auth):
    return get_user_guardians(me["id"])


@app.get("/wards", response_model=List[GuardianPersonResponse], tags=["guardians"],
         summary="Мои подопечные",
         description="Пользователи, за которыми я слежу как опекун.")
def my_wards_endpoint(me: dict = Auth):
    return get_user_wards(me["id"])


@app.post("/guardians/attach/{patient_user_id}", response_model=GuardianInviteResponse,
          status_code=202, tags=["guardians"],
          summary="Запросить опекунство над пользователем",
          description="Создаёт приглашение. Опекун (вы) должен подтвердить его в Telegram.")
def attach_as_guardian_endpoint(
    patient_user_id: int,
    body: GuardianAttachRequest,
    me: dict = Auth,
):
    return _create_guardian_invite_flow(
        patient_user_id, me["id"], body.relationship, initiated_by="guardian"
    )


@app.post("/guardians/invite", response_model=GuardianInviteResponse, status_code=202,
          tags=["guardians"],
          summary="Пригласить опекуна по email",
          description="Подопечный приглашает пользователя стать опекуном. "
                      "Опекун подтверждает в Telegram.")
def invite_guardian_by_email_endpoint(body: GuardianInviteByEmailRequest, me: dict = Auth):
    guardian = get_user_by_email(body.email.strip())
    if not guardian:
        raise HTTPException(404, "User not found")
    return _create_guardian_invite_flow(
        me["id"], guardian["id"], body.relationship, initiated_by="patient"
    )


@app.delete("/wards/{patient_user_id}", status_code=204, tags=["guardians"],
            summary="Перестать быть опекуном",
            description="Удаляет связь опекунства с подопечным.")
def remove_ward_endpoint(patient_user_id: int, me: dict = Auth):
    if not remove_guardian_link(patient_user_id, me["id"]):
        raise HTTPException(404, "Guardian link not found")
    return Response(status_code=204)


@app.post("/users/{user_id}/guardians", status_code=201, tags=["guardians"],
          summary="Добавить опекуна",
          description="Привязывает одного пользователя как опекуна к другому. "
                      "guardian_id — ID пользователя-опекуна (должен быть зарегистрирован). "
                      "relationship — необязательное описание связи (например: 'дочь', 'врач').")
def add_guardian_endpoint(user_id: int, g: GuardianAdd, _: dict = Auth):
    lid = add_guardian(user_id, g.guardian_id, g.relationship)
    return {"id": lid, "user_id": user_id, "guardian_id": g.guardian_id}


@app.get("/users/{user_id}/guardians", response_model=List[dict], tags=["guardians"],
         summary="Список опекунов",
         description="Возвращает всех опекунов пользователя с их данными и типом связи.")
def get_user_guardians_endpoint(user_id: int, _: dict = Auth):
    return get_user_guardians(user_id)


# ──── Notifications ────

@app.post("/users/{user_id}/notifications", response_model=NotificationResponse, status_code=201,
          tags=["notifications"],
          summary="Создать уведомление",
          description="Создаёт запись в очереди уведомлений. "
                      "Telegram-бот периодически проверяет эту таблицу, "
                      "отправляет сообщение опекуну (guardian_id) в Telegram и удаляет запись. "
                      "schedule_id — к какому приёму привязано, text — текст сообщения.")
def create_notification_endpoint(user_id: int, n: NotificationCreate, _: dict = Auth):
    nid = create_notification(n.schedule_id, n.text, n.guardian_id)
    entry = next((x for x in get_user_notifications(user_id) if x["id"] == nid), None)
    if not entry:
        raise HTTPException(404, "Notification not found after creation")
    return entry


@app.get("/users/{user_id}/notifications", response_model=List[NotificationResponse],
         tags=["notifications"],
         summary="Список уведомлений пользователя",
         description="Возвращает уведомления, ещё не отправленные ботом. "
                     "После отправки бот удаляет записи из таблицы.")
def get_user_notifications_endpoint(user_id: int, limit: Optional[int] = None, _: dict = Auth):
    return get_user_notifications(user_id, limit=limit)
