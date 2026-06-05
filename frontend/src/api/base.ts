import { runUnauthorizedHandler } from './unauthorizedHandler';

const BACKEND_ORIGIN = 'https://pi11box.ru';
// Запросы идут с префиксом /api/ (например /api/auth/me, /api/medications). В dev — relative (proxy на бэкенд), в prod — полный URL
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.DEV ? '' : BACKEND_ORIGIN);

/** Корень сервера — для health GET / */
export function getServerRoot(): string {
  if (API_BASE_URL === '') return BACKEND_ORIGIN;
  const base = API_BASE_URL.replace(/\/api\/?$/, '').replace(/\/$/, '');
  return base || API_BASE_URL;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  // Если endpoint начинается с http:// или https://, используем его как есть
  let url: string;
  if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
    url = endpoint;
  } else {
    // Убеждаемся, что endpoint начинается с / и добавляем префикс /api
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const normalizedEndpoint = path.startsWith('/api/') ? path : `/api${path}`;
    const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
    url = `${baseUrl}${normalizedEndpoint}`;
  }

  const hasBody = options.body != null;
  const response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      ...(hasBody && { 'Content-Type': 'application/json' }),
      ...options.headers,
    },
  });

  // Для DELETE запросов (204 No Content) возвращаем undefined до проверки ok
  if (response.status === 204) {
    if (!response.ok) {
      throw new ApiError(response.status, `API Error: ${response.statusText}`);
    }
    return undefined as T;
  }

  if (!response.ok) {
    if (response.status === 401) {
      runUnauthorizedHandler();
    }
    // Пытаемся получить сообщение об ошибке из ответа
    let errorMessage = response.statusText;
    try {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const errorData = (await response.json()) as Record<string, unknown>;
        if (response.status === 422 && Array.isArray(errorData.detail)) {
          const parts = (errorData.detail as Array<{ msg?: string }>)
            .map(d => d.msg)
            .filter((m): m is string => typeof m === 'string');
          errorMessage = parts.length > 0 ? parts.join('. ') : errorMessage;
        } else {
          errorMessage = (errorData.error as string) || errorMessage;
        }
      }
    } catch {
      // Игнорируем ошибки парсинга
    }
    throw new ApiError(response.status, errorMessage);
  }

  // Проверяем, есть ли контент для парсинга
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    const text = await response.text();
    if (!text || text.trim() === '') {
      return undefined as T;
    }
    return JSON.parse(text);
  }

  return undefined as T;
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint, { method: 'GET' }),

  post: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  put: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  patch: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' }),
};
