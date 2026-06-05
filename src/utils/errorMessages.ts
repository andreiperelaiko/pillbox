/**
 * Преобразует сообщения об ошибках API в понятный текст на русском.
 */
export function toUserFriendlyError(message: string, status?: number): string {
  const lower = message.toLowerCase();

  // По коду ответа (если сообщение не задано или общее)
  if (status !== undefined) {
    if (status === 401) return 'Сессия истекла. Войдите снова.';
    if (status === 403) return 'Недостаточно прав для этого действия.';
    if (status === 404) return 'Не найдено.';
    if (status >= 500) return 'Ошибка сервера. Попробуйте позже.';
    if (status === 422 && (!message || message === 'Unprocessable Entity')) return 'Ошибка валидации. Проверьте введённые данные.';
    if (status >= 400) return message || 'Ошибка запроса. Проверьте данные.';
  }

  // Сообщения валидации (422 / Pydantic)
  if (lower.includes('not a valid email') || lower.includes('value is not a valid email'))
    return 'Некорректный email.';
  if (lower.includes('at least') && lower.includes('character')) return 'Пароль слишком короткий.';
  if (lower.includes('field required')) return 'Заполните обязательные поля.';

  // Типичные фразы с бэкенда (англ)
  if (lower.includes('invalid') && (lower.includes('credential') || lower.includes('password')))
    return 'Неверный email или пароль.';
  if (lower.includes('invalid') && lower.includes('email')) return 'Некорректный email.';
  if (lower.includes('user already exists') || lower.includes('already registered'))
    return 'Пользователь с таким email уже зарегистрирован.';
  if (lower.includes('unauthorized') || lower.includes('not authenticated'))
    return 'Требуется вход в аккаунт.';
  if (lower.includes('network') || lower.includes('fetch') || lower.includes('failed to fetch'))
    return 'Нет связи с сервером. Проверьте интернет.';
  if (lower.includes('timeout')) return 'Превышено время ожидания. Попробуйте снова.';

  // Если сообщение уже похоже на русский — вернуть как есть
  if (/[а-яё]/i.test(message)) return message;

  return message || 'Произошла ошибка. Попробуйте ещё раз.';
}
