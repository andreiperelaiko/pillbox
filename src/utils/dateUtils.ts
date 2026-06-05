/**
 * Форматирует дату в локальной временной зоне как YYYY-MM-DD (для query-параметров и input[type="date"]).
 * Использовать вместо date.toISOString().split('T')[0], чтобы избежать сдвига на день из-за UTC.
 */
export function formatDateLocal(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}
