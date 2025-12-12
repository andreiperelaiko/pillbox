import { api } from './base';
import type { Caregiver } from '../types';

export const caregiversApi = {
  getAll: () => api.get<Caregiver[]>('/caregivers'),

  getById: (id: string) => api.get<Caregiver>(`/caregivers/${id}`),

  create: (data: Omit<Caregiver, 'id' | 'createdAt'>) => api.post<Caregiver>('/caregivers', data),

  update: (id: string, data: Partial<Omit<Caregiver, 'id' | 'createdAt'>>) =>
    api.patch<Caregiver>(`/caregivers/${id}`, data),

  delete: (id: string) => api.delete<void>(`/caregivers/${id}`),
};
