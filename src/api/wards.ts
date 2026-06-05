import { api } from './base';

/** Ответ GET /api/wards — подопечный (пользователь, для которого вы опекун). */
export interface WardResponse {
  id: number;
  email: string;
  name: string;
  relationship: string | null;
}

/**
 * GET /api/wards — мои подопечные. 200: WardResponse[]
 * DELETE /api/wards/{user_id} — отказаться от опекунства. 204.
 */
export const wardsApi = {
  getMyWards: () => api.get<WardResponse[]>('/wards'),
  removeWard: (userId: number) => api.delete<void>(`/wards/${userId}`),
};
