let handler: (() => void) | null = null;
let lastRun = 0;
const COOLDOWN_MS = 3000;

export function setUnauthorizedHandler(fn: (() => void) | null): void {
  handler = fn;
}

export function runUnauthorizedHandler(): void {
  const now = Date.now();
  if (now - lastRun < COOLDOWN_MS) return;
  lastRun = now;
  if (handler) handler();
}
