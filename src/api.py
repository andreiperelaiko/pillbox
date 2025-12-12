from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
import re
from src.db import (
    # Medications
    get_all_medications,
    get_medication,
    create_medication,
    update_medication,
    delete_medication,
    # Intakes
    get_all_intakes,
    get_intake,
    create_intake,
    update_intake,
    delete_intake,
    confirm_medication_in_intake,
    # Caregivers
    get_all_caregivers,
    get_caregiver,
    create_caregiver,
    update_caregiver,
    delete_caregiver,
    # Settings
    get_settings,
    update_settings,
)

app = FastAPI(title="Pillbox API", version="1.0.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ==================== MODELS ====================

class MedicationCreate(BaseModel):
    name: str
    form: str
    defaultAmount: Optional[int] = 1
    imageUrl: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name is required')
        return v.strip()

    @field_validator('form')
    @classmethod
    def validate_form(cls, v):
        valid_forms = ['таблетки', 'капсулы', 'жидкость', 'укол', 'порошок', 'мазь', 'спрей']
        if v not in valid_forms:
            raise ValueError(f'Invalid form. Must be one of: {", ".join(valid_forms)}')
        return v

    @field_validator('defaultAmount')
    @classmethod
    def validate_default_amount(cls, v):
        if v is not None and (not isinstance(v, int) or v < 1):
            raise ValueError('defaultAmount must be a positive number >= 1')
        return v or 1

    @field_validator('imageUrl')
    @classmethod
    def validate_image_url(cls, v):
        return v.strip() if v else None


class MedicationResponse(BaseModel):
    id: str
    name: str
    form: str
    defaultAmount: int
    imageUrl: Optional[str]
    createdAt: int


class MedicationDose(BaseModel):
    medicationId: str
    amount: int
    unit: str
    confirmed: bool = False

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if not isinstance(v, int) or v < 1:
            raise ValueError('amount must be a positive number >= 1')
        return v


class IntakeCreate(BaseModel):
    dateTime: int
    medications: List[MedicationDose]
    seriesId: Optional[str] = None

    @field_validator('dateTime')
    @classmethod
    def validate_date_time(cls, v):
        if not isinstance(v, int) or v <= 0:
            raise ValueError('dateTime must be a valid positive timestamp')
        return v

    @field_validator('medications')
    @classmethod
    def validate_medications(cls, v):
        if not v or len(v) == 0:
            raise ValueError('medications array must not be empty')
        return v


class IntakeResponse(BaseModel):
    id: str
    dateTime: int
    medications: List[MedicationDose]
    createdAt: int
    seriesId: Optional[str] = None


class CaregiverCreate(BaseModel):
    name: str
    phone: str
    email: EmailStr
    telegram: str

    @field_validator('name', 'phone', 'telegram')
    @classmethod
    def validate_non_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field must be non-empty')
        return v.strip()

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.strip()


class CaregiverResponse(BaseModel):
    id: str
    name: str
    phone: str
    email: str
    telegram: str
    createdAt: int


class SettingsResponse(BaseModel):
    notificationDelayMinutes: int


class SettingsUpdate(BaseModel):
    notificationDelayMinutes: Optional[int] = None

    @field_validator('notificationDelayMinutes')
    @classmethod
    def validate_delay(cls, v):
        if v is not None and (not isinstance(v, int) or v < 0):
            raise ValueError('notificationDelayMinutes must be a non-negative number')
        return v


# ==================== ERROR HANDLERS ====================

def error_response(message: str):
    return {"error": message}


# ==================== MEDICATIONS ENDPOINTS ====================

@app.get("/api/medications", response_model=List[MedicationResponse])
def get_medications():
    """Получить список всех медикаментов"""
    try:
        return get_all_medications()
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.get("/api/medications/{medication_id}", response_model=MedicationResponse)
def get_medication_by_id(medication_id: str):
    """Получить медикамент по ID"""
    try:
        medication = get_medication(medication_id)
        if not medication:
            raise HTTPException(status_code=404, detail=error_response("Medication not found"))
        return medication
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.post("/api/medications", response_model=MedicationResponse, status_code=201)
def create_medication_endpoint(medication: MedicationCreate):
    """Создать новый медикамент"""
    try:
        medication_id = create_medication(
            name=medication.name,
            form=medication.form,
            default_amount=medication.defaultAmount,
            image_url=medication.imageUrl
        )
        created = get_medication(medication_id)
        if not created:
            raise HTTPException(status_code=500, detail=error_response("Failed to retrieve created medication"))
        return created
    except ValueError as e:
        raise HTTPException(status_code=400, detail=error_response(str(e)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.patch("/api/medications/{medication_id}", response_model=MedicationResponse)
def update_medication_endpoint(medication_id: str, medication: dict):
    """Обновить медикамент"""
    try:
        # Валидация form если передан
        if 'form' in medication:
            valid_forms = ['таблетки', 'капсулы', 'жидкость', 'укол', 'порошок', 'мазь', 'спрей']
            if medication['form'] not in valid_forms:
                raise HTTPException(
                    status_code=400,
                    detail=error_response(f"Invalid form. Must be one of: {', '.join(valid_forms)}")
                )
        
        # Валидация defaultAmount если передан
        if 'defaultAmount' in medication:
            if not isinstance(medication['defaultAmount'], int) or medication['defaultAmount'] < 1:
                raise HTTPException(
                    status_code=400,
                    detail=error_response("defaultAmount must be a positive number >= 1")
                )
        
        updated = update_medication(
            medication_id=medication_id,
            name=medication.get('name'),
            form=medication.get('form'),
            default_amount=medication.get('defaultAmount'),
            image_url=medication.get('imageUrl')
        )
        if not updated:
            raise HTTPException(status_code=404, detail=error_response("Medication not found"))
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.delete("/api/medications/{medication_id}", status_code=204)
def delete_medication_endpoint(medication_id: str):
    """Удалить медикамент"""
    try:
        deleted = delete_medication(medication_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=error_response("Medication not found"))
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


# ==================== INTAKES ENDPOINTS ====================

@app.get("/api/intakes", response_model=List[IntakeResponse])
def get_intakes():
    """Получить список всех приемов"""
    try:
        return get_all_intakes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.get("/api/intakes/{intake_id}", response_model=IntakeResponse)
def get_intake_by_id(intake_id: str):
    """Получить прием по ID"""
    try:
        intake = get_intake(intake_id)
        if not intake:
            raise HTTPException(status_code=404, detail=error_response("Intake not found"))
        return intake
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.post("/api/intakes", response_model=IntakeResponse, status_code=201)
def create_intake_endpoint(intake: IntakeCreate):
    """Создать новый прием"""
    try:
        # Валидация medications
        if not intake.medications:
            raise HTTPException(
                status_code=400,
                detail=error_response("medications array must not be empty")
            )
        
        for med in intake.medications:
            if not med.medicationId:
                raise HTTPException(
                    status_code=400,
                    detail=error_response("Each medication must have a medicationId")
                )
            if not isinstance(med.amount, int) or med.amount < 1:
                raise HTTPException(
                    status_code=400,
                    detail=error_response("Each medication must have a valid positive amount")
                )
            if not med.unit:
                raise HTTPException(
                    status_code=400,
                    detail=error_response("Each medication must have a unit")
                )
        
        medications_data = [med.model_dump() for med in intake.medications]
        
        intake_id = create_intake(
            date_time=intake.dateTime,
            medications=medications_data,
            series_id=intake.seriesId
        )
        created = get_intake(intake_id)
        if not created:
            raise HTTPException(status_code=500, detail=error_response("Failed to retrieve created intake"))
        return created
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=error_response(str(e)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.patch("/api/intakes/{intake_id}", response_model=IntakeResponse)
def update_intake_endpoint(intake_id: str, intake: dict):
    """Обновить прием"""
    try:
        # Валидация dateTime если передан
        if 'dateTime' in intake:
            if not isinstance(intake['dateTime'], int) or intake['dateTime'] <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=error_response("dateTime must be a valid positive timestamp")
                )
        
        # Валидация medications если передан
        if 'medications' in intake:
            if not isinstance(intake['medications'], list) or len(intake['medications']) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=error_response("medications must be a non-empty array")
                )
            
            for med in intake['medications']:
                if not med.get('medicationId'):
                    raise HTTPException(
                        status_code=400,
                        detail=error_response("Each medication must have a medicationId")
                    )
                if not isinstance(med.get('amount'), int) or med.get('amount', 0) < 1:
                    raise HTTPException(
                        status_code=400,
                        detail=error_response("Each medication must have a valid positive amount")
                    )
                if not med.get('unit'):
                    raise HTTPException(
                        status_code=400,
                        detail=error_response("Each medication must have a unit")
                    )
        
        updated = update_intake(
            intake_id=intake_id,
            date_time=intake.get('dateTime'),
            medications=intake.get('medications')
        )
        if not updated:
            raise HTTPException(status_code=404, detail=error_response("Intake not found"))
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.delete("/api/intakes/{intake_id}", status_code=204)
def delete_intake_endpoint(intake_id: str):
    """Удалить прием"""
    try:
        deleted = delete_intake(intake_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=error_response("Intake not found"))
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.patch("/api/intakes/{intake_id}/medications/{medication_id}/confirm", response_model=IntakeResponse)
def confirm_medication_endpoint(intake_id: str, medication_id: str):
    """Подтвердить прием медикамента в приеме"""
    try:
        updated = confirm_medication_in_intake(intake_id, medication_id)
        if not updated:
            raise HTTPException(
                status_code=404,
                detail=error_response("Intake not found or medication not found in intake")
            )
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


# ==================== CAREGIVERS ENDPOINTS ====================

@app.get("/api/caregivers", response_model=List[CaregiverResponse])
def get_caregivers():
    """Получить список всех опекунов"""
    try:
        return get_all_caregivers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.get("/api/caregivers/{caregiver_id}", response_model=CaregiverResponse)
def get_caregiver_by_id(caregiver_id: str):
    """Получить опекуна по ID"""
    try:
        caregiver = get_caregiver(caregiver_id)
        if not caregiver:
            raise HTTPException(status_code=404, detail=error_response("Caregiver not found"))
        return caregiver
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.post("/api/caregivers", response_model=CaregiverResponse, status_code=201)
def create_caregiver_endpoint(caregiver: CaregiverCreate):
    """Создать нового опекуна"""
    try:
        caregiver_id = create_caregiver(
            name=caregiver.name,
            phone=caregiver.phone,
            email=caregiver.email,
            telegram=caregiver.telegram
        )
        created = get_caregiver(caregiver_id)
        if not created:
            raise HTTPException(status_code=500, detail=error_response("Failed to retrieve created caregiver"))
        return created
    except ValueError as e:
        raise HTTPException(status_code=400, detail=error_response(str(e)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.patch("/api/caregivers/{caregiver_id}", response_model=CaregiverResponse)
def update_caregiver_endpoint(caregiver_id: str, caregiver: dict):
    """Обновить опекуна"""
    try:
        # Валидация email если передан
        if 'email' in caregiver:
            email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_pattern, caregiver['email']):
                raise HTTPException(
                    status_code=400,
                    detail=error_response("Invalid email format")
                )
        
        updated = update_caregiver(
            caregiver_id=caregiver_id,
            name=caregiver.get('name'),
            phone=caregiver.get('phone'),
            email=caregiver.get('email'),
            telegram=caregiver.get('telegram')
        )
        if not updated:
            raise HTTPException(status_code=404, detail=error_response("Caregiver not found"))
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.delete("/api/caregivers/{caregiver_id}", status_code=204)
def delete_caregiver_endpoint(caregiver_id: str):
    """Удалить опекуна"""
    try:
        deleted = delete_caregiver(caregiver_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=error_response("Caregiver not found"))
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


# ==================== SETTINGS ENDPOINTS ====================

@app.get("/api/settings", response_model=SettingsResponse)
def get_settings_endpoint():
    """Получить настройки"""
    try:
        return get_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


@app.patch("/api/settings", response_model=SettingsResponse)
def update_settings_endpoint(settings: SettingsUpdate):
    """Обновить настройки"""
    try:
        return update_settings(settings.notificationDelayMinutes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=error_response(str(e)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response(str(e)))


# ==================== ROOT ====================

@app.get("/")
def root():
    return {"message": "Pillbox API", "version": "1.0.0"}
