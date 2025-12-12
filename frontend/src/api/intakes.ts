import { api } from './base';
import type { MedicationIntake } from '../types';

export const intakesApi = {
  getAll: () => api.get<MedicationIntake[]>('/intakes'),

  getById: (id: string) => api.get<MedicationIntake>(`/intakes/${id}`),

  create: (data: Omit<MedicationIntake, 'id' | 'createdAt'>) =>
    api.post<MedicationIntake>('/intakes', data),

  update: (id: string, data: Partial<Omit<MedicationIntake, 'id' | 'createdAt'>>) =>
    api.patch<MedicationIntake>(`/intakes/${id}`, data),

  delete: (id: string) => api.delete<void>(`/intakes/${id}`),

  confirmMedication: (intakeId: string, medicationId: string) =>
    api.patch<MedicationIntake>(`/intakes/${intakeId}/medications/${medicationId}/confirm`, {}),
};
