from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.db import (
    get_user, get_user_by_email,
    create_medication, get_medications, get_medication,
    create_schedule, get_medication_schedules, log_medication_taken,
    add_guardian, get_user_guardians,
    create_notification, get_user_notifications,
    create_user_with_password, get_auth_user_by_email,
    create_session, delete_session, delete_user_sessions,
)
from src.auth import (
    SESSION_COOKIE_NAME, clear_session_cookie, create_session_id,
    get_current_user, get_session_expiry, hash_password,
    set_session_cookie, verify_password,
)
app = FastAPI(title="Pillbox API", version="1.0.0",
              description="API для управления приёмом лекарств, расписаниями и уведомлениями. "
                          "Все эндпоинты кроме /auth/register и /auth/login требуют cookie-сессию. "
                          "Сначала вызовите /auth/login — cookie установится автоматически.")

Auth = Depends(get_current_user)


# ──── Models ────

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    phone: Optional[str]
    telegram: Optional[str]
    telegram_chat_id: Optional[str]

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
    uid = create_user_with_password(p.email, p.name, hash_password(p.password), p.phone, p.telegram)
    user = get_user(uid)
    if not user:
        raise HTTPException(404, "User not found after creation")
    return user


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
    return me


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
    return user


@app.get("/users/email/{email}", response_model=UserResponse, tags=["users"],
         summary="Найти пользователя по email",
         description="Поиск пользователя по точному совпадению email. Возвращает 404 если не найден.")
def get_user_by_email_endpoint(email: str, _: dict = Auth):
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(404, "User not found")
    return user


# ──── Medications ────

@app.post("/medications", response_model=MedicationResponse, status_code=201, tags=["medications"],
          summary="Создать препарат",
          description="Добавляет новый препарат в справочник. "
                      "Содержит только название и описание. Дозировка указывается при создании расписания.")
def create_medication_endpoint(m: MedicationCreate, _: dict = Auth):
    mid = create_medication(m.name, m.description)
    med = get_medication(mid)
    if not med:
        raise HTTPException(404, "Medication not found after creation")
    return med


@app.get("/medications", response_model=List[MedicationResponse], tags=["medications"],
         summary="Список всех препаратов",
         description="Возвращает все препараты из справочника, отсортированные по названию.")
def get_medications_endpoint(_: dict = Auth):
    return get_medications()


@app.get("/medications/{medication_id}", response_model=MedicationResponse, tags=["medications"],
         summary="Получить препарат по ID",
         description="Возвращает название и описание препарата. 404 если не найден.")
def get_medication_endpoint(medication_id: int, _: dict = Auth):
    med = get_medication(medication_id)
    if not med:
        raise HTTPException(404, "Medication not found")
    return med


# ──── Schedules ────

@app.post("/medications/{medication_id}/schedules", response_model=ScheduleResponse, status_code=201,
          tags=["schedules"],
          summary="Создать запись в расписании",
          description="Добавляет приём: когда принять (intake_at) и в какой дозе (dose). "
                      "Поле taken по умолчанию false — означает что приём ещё не выполнен.")
def create_schedule_endpoint(medication_id: int, s: ScheduleCreate, _: dict = Auth):
    sid = create_schedule(medication_id, s.intake_at, s.dose)
    entry = next((x for x in get_medication_schedules(medication_id) if x["id"] == sid), None)
    if not entry:
        raise HTTPException(404, "Schedule not found after creation")
    return entry


@app.get("/medications/{medication_id}/schedules", response_model=List[ScheduleResponse],
         tags=["schedules"],
         summary="Расписание препарата",
         description="Все записи расписания для данного препарата, отсортированные по дате. "
                     "taken=true — приём выполнен, taken=false — ещё нет (или пропущен).")
def get_medication_schedules_endpoint(medication_id: int, _: dict = Auth):
    return get_medication_schedules(medication_id)


@app.post("/medications/{medication_id}/schedules/mark-taken", response_model=ScheduleResponse,
          tags=["schedules"],
          summary="Отметить приём",
          description="Ставит taken=true для указанного schedule_id. "
                      "Если приём не отмечен — считается пропущенным.")
def mark_taken_endpoint(medication_id: int, body: MarkScheduleRequest, _: dict = Auth):
    uid = log_medication_taken(body.schedule_id)
    if not uid:
        raise HTTPException(404, "Schedule not found")
    entry = next((x for x in get_medication_schedules(medication_id) if x["id"] == uid), None)
    if not entry:
        raise HTTPException(404, "Schedule not found after update")
    return entry


# ──── Guardians ────

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
