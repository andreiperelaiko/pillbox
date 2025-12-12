import { api } from './base';
import type { Medication } from '../types';

export const medicationsApi = {
  getAll: () => api.get<Medication[]>('/medications'),

  getById: (id: string) => api.get<Medication>(`/medications/${id}`),

  create: (data: Omit<Medication, 'id' | 'createdAt'>) =>
    api.post<Medication>('/medications', data),

  update: (id: string, data: Partial<Omit<Medication, 'id' | 'createdAt'>>) =>
    api.patch<Medication>(`/medications/${id}`, data),

  delete: (id: string) => api.delete<void>(`/medications/${id}`),
};
