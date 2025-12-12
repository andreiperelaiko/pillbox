import { api } from './base';
import type { Settings } from '../types';

export const settingsApi = {
  get: () => api.get<Settings>('/settings'),

  update: (data: Partial<Settings>) => api.patch<Settings>('/settings', data),
};
