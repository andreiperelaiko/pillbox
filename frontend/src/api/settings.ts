import { api } from './base';
import type { User } from '../types';

export interface AccountSettings {
  email: string;
  email_verified: boolean;
  telegram: string | null;
  telegram_verified: boolean;
  telegram_bot_url: string;
  site_settings_url: string;
}

export const settingsApi = {
  getAccount: () => api.get<AccountSettings>('/auth/settings'),
  sendEmailVerification: () =>
    api.post<{ message: string }>('/auth/verification/email/send', {}),
  updateTelegram: (telegram: string) =>
    api.patch<User>('/auth/profile', { telegram }),
};
