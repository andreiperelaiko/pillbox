import type { MedicationIntake } from '../types';

export const getRelatedIntakes = (
  intake: MedicationIntake,
  allIntakes: MedicationIntake[]
): {
  previous: MedicationIntake[];
  current: MedicationIntake;
  next: MedicationIntake[];
} | null => {
  // Если у приема нет seriesId, значит он одиночный
  if (!intake.seriesId) {
    return null;
  }

  // Находим все приемы с таким же seriesId
  const related = allIntakes.filter(i => i.seriesId === intake.seriesId);

  if (related.length <= 1) {
    return null;
  }

  // Сортируем по дате
  const sorted = related.sort((a, b) => a.dateTime - b.dateTime);
  const currentIndex = sorted.findIndex(i => i.id === intake.id);

  if (currentIndex === -1) {
    return null;
  }

  return {
    previous: sorted.slice(0, currentIndex),
    current: sorted[currentIndex],
    next: sorted.slice(currentIndex + 1),
  };
};
