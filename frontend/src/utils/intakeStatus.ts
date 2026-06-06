import type { GroupedIntakeView, Settings } from '../types';

export type IntakeStatus = 'completed' | 'completedPast' | 'pending' | 'missed';

export const getIntakeStatus = (
  intake: GroupedIntakeView,
  settings: Settings | undefined
): IntakeStatus => {
  if (!settings) return 'pending';
  const now = Date.now();
  const isPast = intake.dateTime < now;
  const allConfirmed = intake.medications.every(m => m.confirmed);
  const hasUnconfirmed = intake.medications.some(m => !m.confirmed);

  if (allConfirmed) {
    if (isPast) return 'completedPast';
    return 'completed';
  }
  if (isPast && hasUnconfirmed) {
    const delayMs = (settings.notificationDelayMinutes || 1) * 60 * 1000;
    if (now - intake.dateTime > delayMs) return 'missed';
  }
  return 'pending';
};
