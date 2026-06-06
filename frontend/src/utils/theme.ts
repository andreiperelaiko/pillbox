/** Управление темой оформления (светлая / тёмная / для слабовидящих) с сохранением выбора. */

export type Theme = 'light' | 'dark' | 'accessible';

/** Доступные темы с подписями для UI. «accessible» — для слабовидящих. */
export const THEME_OPTIONS: Array<{ value: Theme; label: string; hint: string }> = [
  { value: 'light', label: 'Светлая', hint: 'Обычная светлая тема' },
  { value: 'dark', label: 'Тёмная', hint: 'Тёмная тема' },
  { value: 'accessible', label: 'Для слабовидящих', hint: 'Высокий контраст и крупный шрифт для слабовидящих' },
];

const THEME_KEY = 'tabletnica-theme';

function isTheme(value: unknown): value is Theme {
  return value === 'light' || value === 'dark' || value === 'accessible';
}

/** Тема при запуске: сохранённый выбор пользователя, иначе системная настройка. */
export function getInitialTheme(): Theme {
  if (typeof localStorage !== 'undefined') {
    const stored = localStorage.getItem(THEME_KEY);
    if (isTheme(stored)) return stored;
  }
  if (typeof window !== 'undefined' && window.matchMedia) {
    if (window.matchMedia('(prefers-contrast: more)').matches) return 'accessible';
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
  }
  return 'light';
}

/** Применяет тему к <html> и сохраняет выбор. */
export function applyTheme(theme: Theme): void {
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', theme);
  }
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(THEME_KEY, theme);
  }
}
