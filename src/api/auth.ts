import { api } from './base';
import type { User } from '../types';

/** Тело POST /api/auth/register — email, name, password обязательны (OpenAPI). */
export interface RegisterPayload {
  email: string;
  name: string;
  password: string;
  telegram?: string | null;
}

export interface LoginPayload {
  email: string;
  password: string;
  remember_me?: boolean;
}

/** Ответ POST /auth/login — только сообщение, пользователь через GET /auth/me */
export interface LoginResponse {
  message: string;
}

/** Ответ POST /auth/logout — удаляет сессию из БД и очищает cookie. 200: { message } */
export interface LogoutResponse {
  message: string;
}

/** Ответ POST /auth/logout-all — выйти со всех устройств. 200: { message, sessions_revoked? } */
export interface LogoutAllResponse {
  message: string;
  sessions_revoked?: number;
}

export const authApi = {
  register: (data: RegisterPayload) => api.post<User>('/auth/register', data),
  login: (data: LoginPayload) => api.post<LoginResponse>('/auth/login', data),
  me: () => api.get<User | null>('/auth/me'),
  logout: () => api.post<LogoutResponse>('/auth/logout', {}),
  logoutAll: () => api.post<LogoutAllResponse>('/auth/logout-all', {}),
};

