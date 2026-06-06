import { format } from 'date-fns';
import ru from 'date-fns/locale/ru';

/**
 * Парсит дату/время из API. Если в строке нет часового пояса — считаем UTC.
 */
export function parseApiDateTime(iso: string): Date {
  if (!iso) return new Date(NaN);
  const trimmed = iso.trim();
  if (/[zZ]$/.test(trimmed) || /[+-]\d{2}:\d{2}$/.test(trimmed)) {
    return new Date(trimmed);
  }
  return new Date(`${trimmed}Z`);
}

/**
 * Форматирует дату в локальной временной зоне как YYYY-MM-DD (для query-параметров и input[type="date"]).
 */
export function formatDateLocal(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/** Дата и время в локальной зоне браузера, русская локаль. */
export function formatDateTimeLocal(
  value: Date | string | number,
  pattern = 'd MMMM yyyy, HH:mm'
): string {
  const date = value instanceof Date ? value : parseApiDateTime(String(value));
  if (Number.isNaN(date.getTime())) return '';
  return format(date, pattern, { locale: ru });
}

/** Только время в локальной зоне. */
export function formatTimeLocal(value: Date | string | number): string {
  return formatDateTimeLocal(value, 'HH:mm');
}
