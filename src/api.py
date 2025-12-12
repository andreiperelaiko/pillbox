from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, time
from src.db import (
    create_user,
    get_user,
    get_user_by_email,
    create_medication,
    get_user_medications,
    get_medication,
    create_schedule,
    get_medication_schedules,
    log_medication_taken,
    log_medication_missed,
    get_medication_history,
    get_user_medication_history,
    add_guardian,
    get_user_guardians,
    create_notification,
    get_user_notifications
)

app = FastAPI(title="Pillbox API", version="1.0.0")


class UserCreate(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None
    telegram: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    phone: Optional[str]
    telegram: Optional[str]


class MedicationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dosage: Optional[str] = None
    unit: Optional[str] = None
    quantity: Optional[int] = None


class MedicationResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    dosage: Optional[str]
    unit: Optional[str]
    quantity: Optional[int]


class ScheduleCreate(BaseModel):
    time: str


class ScheduleResponse(BaseModel):
    id: int
    medication_id: int
    time: str


class MedicationLogCreate(BaseModel):
    scheduled_time: datetime
    taken_at: Optional[datetime] = None
    schedule_id: Optional[int] = None


class MedicationLogResponse(BaseModel):
    id: int
    medication_id: int
    schedule_id: Optional[int]
    scheduled_time: datetime
    taken_at: Optional[datetime]


class GuardianAdd(BaseModel):
    guardian_id: int
    relationship: Optional[str] = None


class NotificationCreate(BaseModel):
    notification_type: str
    title: str
    message: str
    guardian_id: Optional[int] = None


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: str
    user_id: Optional[int]
    guardian_id: Optional[int]
    created_at: Optional[datetime]


@app.get("/")
def root():
    return {"message": "Pillbox API", "version": "1.0.0"}


@app.post("/users", response_model=UserResponse, status_code=201)
def create_user_endpoint(user: UserCreate):
    try:
        user_id = create_user(
            email=user.email,
            name=user.name,
            phone=user.phone,
            telegram=user.telegram
        )
        created_user = get_user(user_id)
        if not created_user:
            raise HTTPException(status_code=404, detail="User not found after creation")
        return created_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user_endpoint(user_id: int):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/email/{email}", response_model=UserResponse)
def get_user_by_email_endpoint(email: str):
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/users/{user_id}/medications", response_model=MedicationResponse, status_code=201)
def create_medication_endpoint(user_id: int, medication: MedicationCreate):
    try:
        medication_id = create_medication(
            user_id=user_id,
            name=medication.name,
            description=medication.description,
            dosage=medication.dosage,
            unit=medication.unit,
            quantity=medication.quantity
        )
        created_medication = get_medication(medication_id)
        if not created_medication:
            raise HTTPException(status_code=404, detail="Medication not found after creation")
        return created_medication
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{user_id}/medications", response_model=List[MedicationResponse])
def get_user_medications_endpoint(user_id: int):
    medications = get_user_medications(user_id)
    return medications


@app.get("/medications/{medication_id}", response_model=MedicationResponse)
def get_medication_endpoint(medication_id: int):
    medication = get_medication(medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    return medication


@app.post("/medications/{medication_id}/schedules", response_model=ScheduleResponse, status_code=201)
def create_schedule_endpoint(medication_id: int, schedule: ScheduleCreate):
    try:
        time_obj = datetime.strptime(schedule.time, "%H:%M").time()
        schedule_id = create_schedule(medication_id=medication_id, time=time_obj)
        schedules = get_medication_schedules(medication_id)
        created_schedule = next((s for s in schedules if s['id'] == schedule_id), None)
        if not created_schedule:
            raise HTTPException(status_code=404, detail="Schedule not found after creation")
        return {**created_schedule, 'time': str(created_schedule['time'])}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/medications/{medication_id}/schedules", response_model=List[ScheduleResponse])
def get_medication_schedules_endpoint(medication_id: int):
    schedules = get_medication_schedules(medication_id)
    return [{**s, 'time': str(s['time'])} for s in schedules]


@app.post("/medications/{medication_id}/logs/taken", response_model=MedicationLogResponse, status_code=201)
def log_medication_taken_endpoint(medication_id: int, log: MedicationLogCreate):
    try:
        log_id = log_medication_taken(
            medication_id=medication_id,
            scheduled_time=log.scheduled_time,
            taken_at=log.taken_at,
            schedule_id=log.schedule_id
        )
        history = get_medication_history(medication_id)
        created_log = next((l for l in history if l['id'] == log_id), None)
        if not created_log:
            raise HTTPException(status_code=404, detail="Log not found after creation")
        return created_log
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/medications/{medication_id}/logs/missed", response_model=MedicationLogResponse, status_code=201)
def log_medication_missed_endpoint(medication_id: int, log: MedicationLogCreate):
    try:
        log_id = log_medication_missed(
            medication_id=medication_id,
            scheduled_time=log.scheduled_time,
            schedule_id=log.schedule_id
        )
        history = get_medication_history(medication_id)
        created_log = next((l for l in history if l['id'] == log_id), None)
        if not created_log:
            raise HTTPException(status_code=404, detail="Log not found after creation")
        return created_log
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/medications/{medication_id}/logs", response_model=List[MedicationLogResponse])
def get_medication_history_endpoint(medication_id: int, limit: Optional[int] = None):
    history = get_medication_history(medication_id, limit=limit)
    return history


@app.get("/users/{user_id}/logs", response_model=List[dict])
def get_user_medication_history_endpoint(user_id: int, days: Optional[int] = None):
    history = get_user_medication_history(user_id, days=days)
    return history


@app.post("/users/{user_id}/guardians", status_code=201)
def add_guardian_endpoint(user_id: int, guardian: GuardianAdd):
    try:
        link_id = add_guardian(
            user_id=user_id,
            guardian_id=guardian.guardian_id,
            relationship=guardian.relationship
        )
        return {"id": link_id, "user_id": user_id, "guardian_id": guardian.guardian_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{user_id}/guardians", response_model=List[dict])
def get_user_guardians_endpoint(user_id: int):
    guardians = get_user_guardians(user_id)
    return guardians


@app.post("/users/{user_id}/notifications", response_model=NotificationResponse, status_code=201)
def create_notification_endpoint(user_id: int, notification: NotificationCreate):
    try:
        notification_id = create_notification(
            notification_type=notification.notification_type,
            message=notification.message,
            title=notification.title,
            user_id=user_id,
            guardian_id=notification.guardian_id
        )
        notifications = get_user_notifications(user_id)
        created_notification = next((n for n in notifications if n['id'] == notification_id), None)
        if not created_notification:
            raise HTTPException(status_code=404, detail="Notification not found after creation")
        return created_notification
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{user_id}/notifications", response_model=List[NotificationResponse])
def get_user_notifications_endpoint(user_id: int, limit: Optional[int] = None):
    notifications = get_user_notifications(user_id, limit=limit)
    return notifications

