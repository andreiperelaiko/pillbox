import type { GroupedIntakeView, Settings } from '../types';

export const checkMissedIntakes = (
  intakes: GroupedIntakeView[],
  settings: Settings
): GroupedIntakeView[] => {
  if (!intakes || !Array.isArray(intakes)) return [];
  if (!settings) return [];
  const now = Date.now();
  const delayMs = (settings.notificationDelayMinutes || 1) * 60 * 1000;

  return intakes.filter(intake => {
    const isPast = intake.dateTime < now;
    const isOverdue = now - intake.dateTime > delayMs;
    const hasUnconfirmed = intake.medications.some(m => !m.confirmed);
    return isPast && hasUnconfirmed && isOverdue;
  });
};

export const getUpcomingIntakes = (
  intakes: GroupedIntakeView[]
): GroupedIntakeView[] => {
  if (!intakes || !Array.isArray(intakes)) return [];
  const now = Date.now();
  const oneDay = 24 * 60 * 60 * 1000;

  return intakes
    .filter(intake => {
      const isFuture = intake.dateTime > now;
      const isWithin24Hours = intake.dateTime - now < oneDay;
      const allConfirmed = intake.medications.every(m => m.confirmed);
      return isFuture && isWithin24Hours && !allConfirmed;
    })
    .sort((a, b) => a.dateTime - b.dateTime);
};
