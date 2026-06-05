import { api } from './base';

/** Публичный ответ GET /users/{id} и GET /users/email/{email} — id, email, имя. Telegram скрыт. */
export interface UserPublicResponse {
  id: number;
  email: string;
  name: string;
}

/**
 * GET /users/{user_id} — получить пользователя по ID.
 * GET /users/email/{email} — найти пользователя по email.
 */
export const usersApi = {
  getById: (userId: number) => api.get<UserPublicResponse>(`/users/${userId}`),
  getByEmail: (email: string) =>
    api.get<UserPublicResponse>(`/users/email/${encodeURIComponent(email)}`),
};
