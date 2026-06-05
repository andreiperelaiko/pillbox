/**
 * Клиентская валидация данных форм перед отправкой на бэкенд.
 *
 * Бэкенд (см. https://pi11box.ru/api/docs) не задаёт строгих ограничений
 * (minLength/format) в OpenAPI, кроме обязательных полей и format=date-time
 * у intake_at. Поэтому здесь мы добавляем разумные клиентские проверки,
 * чтобы не отправлять заведомо некорректные данные и давать понятные подсказки.
 *
 * Каждая функция возвращает строку с ошибкой (рус.) или null, если поле валидно.
 */

export type ValidationError = string | null;

/** Ограничения длины — согласованы с UI-подсказками. */
export const LIMITS = {
  passwordMin: 6,
  passwordMax: 128,
  nameMin: 2,
  nameMax: 100,
  medicationNameMax: 200,
  descriptionMax: 1000,
  doseMax: 100,
  relationshipMax: 100,
  telegramMin: 5,
  telegramMax: 32,
} as const;

// Достаточно строгая, но практичная проверка email.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
// Telegram username: латиница/цифры/подчёркивание, с ведущим @ или без.
const TELEGRAM_RE = /^@?[a-zA-Z0-9_]{5,32}$/;

/** Email: обязателен, корректный формат. */
export function validateEmail(value: string): ValidationError {
  const v = value.trim();
  if (!v) return 'Введите email.';
  if (v.length > 254) return 'Email слишком длинный.';
  if (!EMAIL_RE.test(v)) return 'Некорректный email. Пример: example@mail.ru';
  return null;
}

/** Пароль при входе: просто обязателен (длину проверяет сервер). */
export function validateLoginPassword(value: string): ValidationError {
  if (!value) return 'Введите пароль.';
  return null;
}

/** Пароль при регистрации: обязателен, минимальная длина. */
export function validateNewPassword(value: string): ValidationError {
  if (!value) return 'Введите пароль.';
  if (value.length < LIMITS.passwordMin)
    return `Пароль должен быть не короче ${LIMITS.passwordMin} символов.`;
  if (value.length > LIMITS.passwordMax)
    return `Пароль не должен превышать ${LIMITS.passwordMax} символов.`;
  return null;
}

/** Имя пользователя: обязательно, разумная длина. */
export function validateName(value: string): ValidationError {
  const v = value.trim();
  if (!v) return 'Введите имя.';
  if (v.length < LIMITS.nameMin) return `Имя должно быть не короче ${LIMITS.nameMin} символов.`;
  if (v.length > LIMITS.nameMax) return `Имя не должно превышать ${LIMITS.nameMax} символов.`;
  return null;
}

/** Telegram: необязателен, но если указан — должен быть валидным username. */
export function validateTelegram(value: string): ValidationError {
  const v = value.trim();
  if (!v) return null;
  if (!TELEGRAM_RE.test(v))
    return 'Некорректный Telegram. Используйте латиницу, цифры и _, 5–32 символа. Пример: @username';
  return null;
}

/** Название лекарства: обязательно, ограничение длины. */
export function validateMedicationName(value: string): ValidationError {
  const v = value.trim();
  if (!v) return 'Введите название лекарства.';
  if (v.length > LIMITS.medicationNameMax)
    return `Название не должно превышать ${LIMITS.medicationNameMax} символов.`;
  return null;
}

/** Описание лекарства: необязательно, ограничение длины. */
export function validateDescription(value: string): ValidationError {
  if (value.trim().length > LIMITS.descriptionMax)
    return `Описание не должно превышать ${LIMITS.descriptionMax} символов.`;
  return null;
}

/** Дозировка: необязательна, ограничение длины. */
export function validateDose(value: string): ValidationError {
  if (value.trim().length > LIMITS.doseMax)
    return `Дозировка не должна превышать ${LIMITS.doseMax} символов.`;
  return null;
}

/** Степень родства / роль опекуна: необязательна, ограничение длины. */
export function validateRelationship(value: string): ValidationError {
  if (value.trim().length > LIMITS.relationshipMax)
    return `Значение не должно превышать ${LIMITS.relationshipMax} символов.`;
  return null;
}

/** Дата в формате YYYY-MM-DD: обязательна и валидна как календарная дата. */
export function validateDate(value: string, label = 'дату'): ValidationError {
  if (!value) return `Выберите ${label}.`;
  const [y, m, d] = value.split('-').map(Number);
  if (!y || !m || !d) return `Некорректная ${label}.`;
  const date = new Date(y, m - 1, d);
  if (date.getFullYear() !== y || date.getMonth() !== m - 1 || date.getDate() !== d)
    return `Некорректная ${label}.`;
  return null;
}

/** Время в формате HH:MM. */
export function validateTime(value: string): ValidationError {
  if (!value) return 'Выберите время приёма.';
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(value)) return 'Некорректное время.';
  return null;
}

/**
 * Проверка периода: обе даты валидны и начало не позже конца.
 * Возвращает ошибку для поля «конец периода» либо null.
 */
export function validateDateRange(start: string, end: string): ValidationError {
  const startErr = validateDate(start, 'дату начала');
  if (startErr) return startErr;
  const endErr = validateDate(end, 'дату окончания');
  if (endErr) return endErr;
  if (end < start) return 'Дата окончания не может быть раньше даты начала.';
  return null;
}

/**
 * Есть ли хотя бы одна ошибка в карте ошибок (значения — строки/null/undefined).
 * Принимает любой объект (в т.ч. interface с фиксированными полями).
 */
export function hasErrors(errors: object): boolean {
  return Object.values(errors).some(Boolean);
}
