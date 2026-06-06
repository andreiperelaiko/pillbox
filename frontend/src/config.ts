/** Vite `base` (e.g. `/site/`). Trailing slash included. */
export const APP_BASE = import.meta.env.BASE_URL;

/** React Router basename without trailing slash (e.g. `/site`). */
export const APP_BASENAME = APP_BASE.replace(/\/$/, '');

export function appUrl(path: string): string {
  const segment = path.startsWith('/') ? path.slice(1) : path;
  return `${APP_BASE}${segment}`.replace(/\/+/g, '/');
}
