import { getServerRoot } from './base';

/**
 * Проверка доступности API: GET / (health).
 * Не бросает исключений, не отправляет credentials.
 */
export async function checkHealth(): Promise<boolean> {
  const root = getServerRoot();
  const url = root.endsWith('/') ? root : `${root}/`;
  try {
    const response = await fetch(url, {
      method: 'GET',
      credentials: 'omit',
    });
    return response.ok;
  } catch {
    return false;
  }
}
