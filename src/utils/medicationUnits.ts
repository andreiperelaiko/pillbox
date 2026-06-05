import type { MedicationForm, DosageUnit } from '../types';

export const getUnitByForm = (form: MedicationForm): DosageUnit => {
  const unitMap: Record<MedicationForm, DosageUnit> = {
    таблетки: 'таблетки',
    капсулы: 'капсулы',
    жидкость: 'мл',
    укол: 'уколы',
    порошок: 'г',
    мазь: 'г',
    спрей: 'мл',
  };
  return unitMap[form] || 'таблетки';
};
