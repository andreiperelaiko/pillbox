import { api } from './base';
import type { MedicationApiItem } from '../types';

/** Тело POST /api/medications — name обязателен, description необязателен */
export interface CreateMedicationPayload {
  name: string;
  description?: string | null;
}

/**
 * GET /medications — список. GET /medications/{medication_id} — по ID. POST /medications — создать.
 */
export const medicationsApi = {
  getAll: () => api.get<MedicationApiItem[]>('/medications'),
  getById: (medicationId: number) => api.get<MedicationApiItem>(`/medications/${medicationId}`),
  create: (data: CreateMedicationPayload) =>
    api.post<MedicationApiItem>('/medications', data),
};
