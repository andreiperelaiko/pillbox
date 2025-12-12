import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import psycopg
from psycopg.rows import dict_row
import json


def get_conn():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg.connect(database_url)
    
    dbname = os.getenv("POSTGRES_DB", "pillboxdb")
    user = os.getenv("POSTGRES_USER", "pillbox")
    password = os.getenv("POSTGRES_PASSWORD", "password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    
    return psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )


# ==================== MEDICATIONS ====================

def get_all_medications() -> List[Dict[str, Any]]:
    """Получить все медикаменты"""
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT 
                    id::text,
                    name,
                    form,
                    default_amount as "defaultAmount",
                    image_url as "imageUrl",
                    created_at as "createdAt"
                FROM medications
                ORDER BY created_at DESC
            """)
            return cur.fetchall()


def get_medication(medication_id: str) -> Optional[Dict[str, Any]]:
    """Получить медикамент по ID"""
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT 
                    id::text,
                    name,
                    form,
                    default_amount as "defaultAmount",
                    image_url as "imageUrl",
                    created_at as "createdAt"
                FROM medications
                WHERE id = %s
            """, (medication_id,))
            return cur.fetchone()


def create_medication(
    name: str,
    form: str,
    default_amount: Optional[int] = None,
    image_url: Optional[str] = None
) -> str:
    """Создать новый медикамент"""
    medication_id = str(uuid.uuid4())
    created_at = int(datetime.now().timestamp() * 1000)
    default_amount = default_amount if default_amount is not None else 1
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO medications (id, name, form, default_amount, image_url, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (medication_id, name.strip(), form, default_amount, image_url.strip() if image_url else None, created_at))
            conn.commit()
            return medication_id


def update_medication(
    medication_id: str,
    name: Optional[str] = None,
    form: Optional[str] = None,
    default_amount: Optional[int] = None,
    image_url: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Обновить медикамент"""
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = %s")
        params.append(name.strip())
    if form is not None:
        updates.append("form = %s")
        params.append(form)
    if default_amount is not None:
        updates.append("default_amount = %s")
        params.append(default_amount)
    if image_url is not None:
        updates.append("image_url = %s")
        params.append(image_url.strip() if image_url else None)
    
    if not updates:
        return get_medication(medication_id)
    
    params.append(medication_id)
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE medications
                SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            conn.commit()
            return get_medication(medication_id)


def delete_medication(medication_id: str) -> bool:
    """Удалить медикамент"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM medications WHERE id = %s", (medication_id,))
            deleted = cur.rowcount > 0
            conn.commit()
            return deleted


# ==================== INTAKES ====================

def get_all_intakes() -> List[Dict[str, Any]]:
    """Получить все приемы"""
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT 
                    id::text,
                    date_time as "dateTime",
                    medications,
                    created_at as "createdAt",
                    series_id::text as "seriesId"
                FROM intakes
                ORDER BY date_time DESC
            """)
            results = cur.fetchall()
            # Преобразуем JSONB в Python dict
            for result in results:
                if result['medications']:
                    result['medications'] = json.loads(result['medications']) if isinstance(result['medications'], str) else result['medications']
            return results


def get_intake(intake_id: str) -> Optional[Dict[str, Any]]:
    """Получить прием по ID"""
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT 
                    id::text,
                    date_time as "dateTime",
                    medications,
                    created_at as "createdAt",
                    series_id::text as "seriesId"
                FROM intakes
                WHERE id = %s
            """, (intake_id,))
            result = cur.fetchone()
            if result and result['medications']:
                result['medications'] = json.loads(result['medications']) if isinstance(result['medications'], str) else result['medications']
            return result


def create_intake(
    date_time: int,
    medications: List[Dict[str, Any]],
    series_id: Optional[str] = None
) -> str:
    """Создать новый прием"""
    intake_id = str(uuid.uuid4())
    created_at = int(datetime.now().timestamp() * 1000)
    medications_json = json.dumps(medications)
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO intakes (id, date_time, medications, created_at, series_id)
                VALUES (%s, %s, %s::jsonb, %s, %s)
                RETURNING id
            """, (intake_id, date_time, medications_json, created_at, series_id))
            conn.commit()
            return intake_id


def update_intake(
    intake_id: str,
    date_time: Optional[int] = None,
    medications: Optional[List[Dict[str, Any]]] = None
) -> Optional[Dict[str, Any]]:
    """Обновить прием"""
    # Получаем текущий прием для сохранения confirmed статусов
    current_intake = get_intake(intake_id)
    if not current_intake:
        return None
    
    updates = []
    params = []
    
    if date_time is not None:
        updates.append("date_time = %s")
        params.append(date_time)
    
    if medications is not None:
        # Сохраняем confirmed статусы для существующих медикаментов
        current_medications = {med['medicationId']: med for med in current_intake['medications']}
        for med in medications:
            if med['medicationId'] in current_medications:
                med['confirmed'] = current_medications[med['medicationId']].get('confirmed', False)
            else:
                med['confirmed'] = med.get('confirmed', False)
        
        medications_json = json.dumps(medications)
        updates.append("medications = %s::jsonb")
        params.append(medications_json)
    
    if not updates:
        return current_intake
    
    params.append(intake_id)
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE intakes
                SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            conn.commit()
            return get_intake(intake_id)


def delete_intake(intake_id: str) -> bool:
    """Удалить прием"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM intakes WHERE id = %s", (intake_id,))
            deleted = cur.rowcount > 0
            conn.commit()
            return deleted


def confirm_medication_in_intake(intake_id: str, medication_id: str) -> Optional[Dict[str, Any]]:
    """Подтвердить прием медикамента в приеме"""
    intake = get_intake(intake_id)
    if not intake:
        return None
    
    medications = intake['medications']
    found = False
    
    for med in medications:
        if med['medicationId'] == medication_id:
            med['confirmed'] = True
            found = True
            break
    
    if not found:
        return None
    
    medications_json = json.dumps(medications)
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE intakes
                SET medications = %s::jsonb
                WHERE id = %s
            """, (medications_json, intake_id))
            conn.commit()
            return get_intake(intake_id)


# ==================== CAREGIVERS ====================

def get_all_caregivers() -> List[Dict[str, Any]]:
    """Получить всех опекунов"""
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT 
                    id::text,
                    name,
                    phone,
                    email,
                    telegram,
                    created_at as "createdAt"
                FROM caregivers
                ORDER BY created_at DESC
            """)
            return cur.fetchall()


def get_caregiver(caregiver_id: str) -> Optional[Dict[str, Any]]:
    """Получить опекуна по ID"""
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT 
                    id::text,
                    name,
                    phone,
                    email,
                    telegram,
                    created_at as "createdAt"
                FROM caregivers
                WHERE id = %s
            """, (caregiver_id,))
            return cur.fetchone()


def create_caregiver(
    name: str,
    phone: str,
    email: str,
    telegram: str
) -> str:
    """Создать нового опекуна"""
    caregiver_id = str(uuid.uuid4())
    created_at = int(datetime.now().timestamp() * 1000)
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO caregivers (id, name, phone, email, telegram, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (caregiver_id, name.strip(), phone.strip(), email.strip(), telegram.strip(), created_at))
            conn.commit()
            return caregiver_id


def update_caregiver(
    caregiver_id: str,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    telegram: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Обновить опекуна"""
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = %s")
        params.append(name.strip())
    if phone is not None:
        updates.append("phone = %s")
        params.append(phone.strip())
    if email is not None:
        updates.append("email = %s")
        params.append(email.strip())
    if telegram is not None:
        updates.append("telegram = %s")
        params.append(telegram.strip())
    
    if not updates:
        return get_caregiver(caregiver_id)
    
    params.append(caregiver_id)
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE caregivers
                SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            conn.commit()
            return get_caregiver(caregiver_id)


def delete_caregiver(caregiver_id: str) -> bool:
    """Удалить опекуна"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM caregivers WHERE id = %s", (caregiver_id,))
            deleted = cur.rowcount > 0
            conn.commit()
            return deleted


# ==================== SETTINGS ====================

def get_settings() -> Dict[str, Any]:
    """Получить настройки"""
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT notification_delay_minutes as "notificationDelayMinutes"
                FROM settings
                WHERE id = 1
            """)
            result = cur.fetchone()
            
            # Если записи нет, возвращаем дефолтные значения
            # (запись должна быть создана при инициализации БД)
            if not result:
                return {"notificationDelayMinutes": 30}
            
            return dict(result)


def update_settings(notification_delay_minutes: Optional[int] = None) -> Dict[str, Any]:
    """Обновить настройки"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            if notification_delay_minutes is not None:
                # Используем UPSERT - создаст если нет, обновит если есть
                cur.execute("""
                    INSERT INTO settings (id, notification_delay_minutes)
                    VALUES (1, %s)
                    ON CONFLICT (id) 
                    DO UPDATE SET notification_delay_minutes = EXCLUDED.notification_delay_minutes
                """, (notification_delay_minutes,))
            conn.commit()
            return get_settings()
