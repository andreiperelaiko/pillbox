import { api } from './base';

/** Ответ GET /guardians — опекун текущего пользователя. */
export interface GuardianResponse {
  id: number;
  email: string;
  name: string;
  relationship: string | null;
}

/** Тело POST /guardians/attach/{user_id} — стать опекуном пользователя. */
export interface GuardianAdd {
  relationship?: string | null;
}

/**
 * GET /guardians — опекуны текущего пользователя. 200: GuardianResponse[]
 * POST /guardians/attach/{user_id} — текущий пользователь становится опекуном user_id. 201. 422: Validation Error
 */
export const guardiansApi = {
  getMyGuardians: () => api.get<GuardianResponse[]>('/guardians'),
  attachAsGuardian: (userId: number, data: GuardianAdd) =>
    api.post<void>(`/guardians/attach/${userId}`, data),
};
