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

export interface GuardianInviteResponse {
  id: number;
  status: string;
  message: string;
}

/**
 * GET /guardians — опекуны текущего пользователя
 * POST /guardians/attach/{user_id} — запрос опекунства (подтверждение в TG)
 * POST /guardians/invite — пригласить опекуна по email
 */
export const guardiansApi = {
  getMyGuardians: () => api.get<GuardianResponse[]>('/guardians'),
  attachAsGuardian: (userId: number, data: GuardianAdd) =>
    api.post<GuardianInviteResponse>(`/guardians/attach/${userId}`, data),
  inviteByEmail: (data: GuardianAdd & { email: string }) =>
    api.post<GuardianInviteResponse>('/guardians/invite', data),
};
