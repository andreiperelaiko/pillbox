import type { MedicationForm } from '../types';

export const getMedicationIcon = (form: MedicationForm): string => {
  const icons: Record<MedicationForm, string> = {
    таблетки: '💊',
    капсулы: '💊',
    жидкость: '🧪',
    укол: '💉',
    порошок: '📦',
    мазь: '🧴',
    спрей: '💨',
  };
  return icons[form] || '💊';
};
