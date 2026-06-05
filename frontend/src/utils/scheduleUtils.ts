import type { ScheduleItem } from '../types';
import type { GroupedIntakeView } from '../types';

/** Группирует приёмы по дате-времени (intake_at) для отображения в календаре и карточках. */
export function scheduleItemsToGroupedViews(items: ScheduleItem[]): GroupedIntakeView[] {
  const byTime = new Map<number, ScheduleItem[]>();
  for (const item of items) {
    const t = new Date(item.intake_at).getTime();
    if (!byTime.has(t)) byTime.set(t, []);
    byTime.get(t)!.push(item);
  }
  const result: GroupedIntakeView[] = [];
  byTime.forEach((scheduleItems, dateTime) => {
    result.push({
      id: `group-${dateTime}-${scheduleItems[0].id}`,
      dateTime,
      medications: scheduleItems.map(s => ({
        medicationId: String(s.medication_id),
        confirmed: s.taken,
        scheduleId: s.id,
        doseDisplay: s.dose ?? '',
      })),
    });
  });
  return result.sort((a, b) => a.dateTime - b.dateTime);
}
