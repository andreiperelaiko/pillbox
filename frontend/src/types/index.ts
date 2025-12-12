export type MedicationForm =
  | 'таблетки'
  | 'капсулы'
  | 'жидкость'
  | 'укол'
  | 'порошок'
  | 'мазь'
  | 'спрей';

export type DosageUnit = 'таблетки' | 'мл' | 'мг' | 'уколы' | 'капсулы' | 'г';

export interface Medication {
  id: string;
  name: string;
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

export interface Caregiver {
  id: string;
  name: string;
  phone: string;
  email: string;
  telegram: string;
  createdAt: number;
}

export interface Settings {
  notificationDelayMinutes: number;
}

export interface AppState {
  medications: Medication[];
  intakes: MedicationIntake[];
  caregivers: Caregiver[];
  settings: Settings;
}
