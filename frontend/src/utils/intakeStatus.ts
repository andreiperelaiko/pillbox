import type { MedicationIntake, Settings } from '../types';

export type IntakeStatus = 'completed' | 'completedPast' | 'pending' | 'missed';

export const getIntakeStatus = (
  intake: MedicationIntake,
  settings: Settings | undefined
): IntakeStatus => {
  if (!settings) {
    return 'pending';
  }
  const now = Date.now();
  const isPast = intake.dateTime < now;
  const allConfirmed = intake.medications.every(m => m.confirmed);
  const hasUnconfirmed = intake.medications.some(m => !m.confirmed);

  // Выполненный - все медикаменты подтверждены
  if (allConfirmed) {
    // Выполненный в прошлом - серый
    if (isPast) {
      return 'completedPast';
    }
    // Выполненный в будущем - зеленый
    return 'completed';
  }

  // Просроченный - прошло время и есть неподтвержденные
  if (isPast && hasUnconfirmed) {
    const delayMs = (settings.notificationDelayMinutes || 30) * 60 * 1000;
    const isOverdue = now - intake.dateTime > delayMs;
    if (isOverdue) {
      return 'missed';
    }
  }

  // Невыполненный, но не просроченный
  return 'pending';
};
