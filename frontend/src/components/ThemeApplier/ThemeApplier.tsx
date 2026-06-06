import { useEffect } from 'react';
import { useAppSelector } from '../../store/hooks';
import type { AppTheme } from '../../types';

const STORAGE_KEY = 'pillbox-theme';

export function getStoredTheme(): AppTheme {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (value === 'dark' || value === 'accessible' || value === 'light') {
      return value;
    }
  } catch {
    // ignore
  }
  return 'light';
}

export function applyTheme(theme: AppTheme) {
  document.documentElement.setAttribute('data-theme', theme);
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // ignore
  }
}

export const ThemeApplier = () => {
  const theme = useAppSelector(state => state.settings.theme);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  return null;
};
