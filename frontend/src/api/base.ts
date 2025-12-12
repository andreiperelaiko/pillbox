// Используем внешний API по умолчанию, можно переопределить через переменную окружения
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://pi11box.ru/api/';

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
    // Убеждаемся, что endpoint начинается с /
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    // Убеждаемся, что API_BASE_URL заканчивается на /, а endpoint начинается с /
    // Чтобы избежать двойных слешей, убираем начальный слеш из endpoint при конкатенации
    const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
    url = `${baseUrl}${normalizedEndpoint}`;
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
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
    // Пытаемся получить сообщение об ошибке из ответа
    let errorMessage = response.statusText;
    try {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const errorData = await response.json();
        errorMessage = errorData.error || errorMessage;
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
