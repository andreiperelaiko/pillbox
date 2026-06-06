export type MedicationForm =
  | 'таблетки'
  | 'капсулы'
  | 'жидкость'
  | 'укол'
  | 'порошок'
  | 'мазь'
  | 'спрей';

export type DosageUnit = 'таблетки' | 'мл' | 'мг' | 'уколы' | 'капсулы' | 'г';

/** Элемент из GET /api/medications (ответ API) */
export interface MedicationApiItem {
  id: number;
  name: string;
  description: string | null;
}

export interface Medication {
  id: string;
  name: string;
  description?: string;
  form: MedicationForm;
  defaultAmount: number;
  imageUrl: string | null;
  createdAt: number;
}

export interface MedicationDose {
  medicationId: string;
  amount: number;
  unit: DosageUnit;
  confirmed: boolean;
}

export interface MedicationIntake {
  id: string;
  dateTime: number; // timestamp
  medications: MedicationDose[];
  createdAt: number;
  seriesId?: string; // Идентификатор серии для связанных приемов
}

/**
 * Приём препарата (один препарат в один приём) из
 * GET /medications/{medication_id}/schedules. taken — выполнен.
 * user_id / notified возвращаются не всегда — необязательны.
 */
export interface ScheduleItem {
  id: number;
  medication_id: number;
  intake_at: string; // ISO 8601
  taken: boolean;
  dose: string | null;
  user_id?: number;
  notified?: boolean;
}

/** Группа приёмов в одно время (для UI): один «приём» = несколько ScheduleItem с одинаковым intake_at */
export interface GroupedIntakeView {
  id: string;
  dateTime: number;
  medications: Array<{
    medicationId: string;
    confirmed: boolean;
    scheduleId: number;
    doseDisplay: string;
  }>;
}

export interface User {
  id: number | string;
  email: string;
  name?: string;
  telegram?: string;
  telegram_chat_id?: string;
  email_verified?: boolean;
  telegram_verified?: boolean;
}

export interface Caregiver {
  id: string;
  name: string;
  phone: string;
  email: string;
  telegram: string;
  createdAt: number;
}

export type AppTheme = 'light' | 'dark' | 'accessible';

export interface Settings {
  notificationDelayMinutes: number;
  theme: AppTheme;
}

/** Опекун из GET /guardians (мои опекуны) */
export interface Guardian {
  id: number;
  email: string;
  name: string;
  relationship: string | null;
}

export interface AppState {
  medications: Medication[];
  schedules: ScheduleItem[];
  guardians: Guardian[];
  settings: Settings;
}
