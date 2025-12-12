import { useState } from 'react';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { createIntake } from '../../store/slices/intakesSlice';
import { Button } from '../Button/Button';
import { Input } from '../Input/Input';
import { Select } from '../Select/Select';
import { getMedicationIcon } from '../../utils/medicationIcons';
import { getUnitByForm } from '../../utils/medicationUnits';
import type { MedicationDose, MedicationForm } from '../../types';
import styles from './AddIntakeModal.module.scss';
import cn from 'classnames';

interface AddIntakeModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialDate?: Date;
}

type ScheduleType = 'single' | 'period' | 'weekdays';

export const AddIntakeModal = ({ isOpen, onClose, initialDate }: AddIntakeModalProps) => {
  const dispatch = useAppDispatch();
  const { items: medications } = useAppSelector(state => state.medications);

  const [scheduleType, setScheduleType] = useState<ScheduleType>('single');
  const [singleDate, setSingleDate] = useState(
    initialDate ? initialDate.toISOString().split('T')[0] : ''
  );
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedWeekdays, setSelectedWeekdays] = useState<number[]>([]);
  const [time, setTime] = useState('09:00');
  const [selectedMedications, setSelectedMedications] = useState<
    Array<{
      medicationId: string;
      amount: string;
    }>
  >([]);
  const [medicationNameFilter, setMedicationNameFilter] = useState('');
  const [medicationTypeFilter, setMedicationTypeFilter] = useState<MedicationForm | 'all'>('all');

  const weekdays = [
    { value: 1, label: 'Пн' },
    { value: 2, label: 'Вт' },
    { value: 3, label: 'Ср' },
    { value: 4, label: 'Чт' },
    { value: 5, label: 'Пт' },
    { value: 6, label: 'Сб' },
    { value: 0, label: 'Вс' },
  ];

  const medicationForms: MedicationForm[] = [
    'таблетки',
    'капсулы',
    'жидкость',
    'укол',
    'порошок',
    'мазь',
    'спрей',
  ];

  const filteredMedications = (medications || []).filter(medication => {
    const matchesName = medication.name.toLowerCase().includes(medicationNameFilter.toLowerCase());
    const matchesType = medicationTypeFilter === 'all' || medication.form === medicationTypeFilter;
    return matchesName && matchesType;
  });

  const toggleMedication = (medicationId: string) => {
    const medication = (medications || []).find(m => m.id === medicationId);
    if (!medication) return;

    const existing = selectedMedications.find(m => m.medicationId === medicationId);
    if (existing) {
      setSelectedMedications(selectedMedications.filter(m => m.medicationId !== medicationId));
    } else {
      setSelectedMedications([
        ...selectedMedications,
        {
          medicationId,
          amount: medication.defaultAmount.toString(),
        },
      ]);
    }
  };

  const updateMedicationAmount = (medicationId: string, amount: string) => {
    setSelectedMedications(
      selectedMedications.map(m => (m.medicationId === medicationId ? { ...m, amount } : m))
    );
  };

  const toggleWeekday = (day: number) => {
    setSelectedWeekdays(
      selectedWeekdays.includes(day)
        ? selectedWeekdays.filter(d => d !== day)
        : [...selectedWeekdays, day]
    );
  };

  const getDatesForSchedule = (): Date[] => {
    const dates: Date[] = [];
    const [hours, minutes] = time.split(':').map(Number);

    if (scheduleType === 'single') {
      if (singleDate) {
        // Используем локальное время для избежания проблем с часовыми поясами
        const [year, month, day] = singleDate.split('-').map(Number);
        const date = new Date(year, month - 1, day, hours, minutes, 0, 0);
        dates.push(date);
      }
    } else if (scheduleType === 'period') {
      if (startDate && endDate) {
        // Парсим даты вручную для избежания проблем с часовыми поясами
        const [startYear, startMonth, startDay] = startDate.split('-').map(Number);
        const [endYear, endMonth, endDay] = endDate.split('-').map(Number);

        // Создаем даты без времени для корректного сравнения
        const start = new Date(startYear, startMonth - 1, startDay);
        const end = new Date(endYear, endMonth - 1, endDay);

        // Нормализуем время для сравнения (ставим на начало дня)
        start.setHours(0, 0, 0, 0);
        end.setHours(0, 0, 0, 0);

        // Итерируем по дням, сравнивая только даты
        const current = new Date(start);
        const endTime = end.getTime();
        let dayCount = 0;

        while (current.getTime() <= endTime) {
          const date = new Date(current);
          date.setHours(hours, minutes, 0, 0);
          dates.push(date);
          dayCount++;

          // Переходим к следующему дню
          current.setDate(current.getDate() + 1);
        }

        console.log(`Generated ${dayCount} dates from ${startDate} to ${endDate}`);
      }
    } else if (scheduleType === 'weekdays') {
      if (selectedWeekdays.length > 0 && startDate && endDate) {
        const [startYear, startMonth, startDay] = startDate.split('-').map(Number);
        const [endYear, endMonth, endDay] = endDate.split('-').map(Number);

        const start = new Date(startYear, startMonth - 1, startDay, 0, 0, 0, 0);
        const end = new Date(endYear, endMonth - 1, endDay, 23, 59, 59, 999);

        const current = new Date(start);
        while (current <= end) {
          const dayOfWeek = current.getDay();
          if (selectedWeekdays.includes(dayOfWeek)) {
            const date = new Date(current);
            date.setHours(hours, minutes, 0, 0);
            dates.push(date);
          }
          // Переходим к следующему дню
          current.setDate(current.getDate() + 1);
        }
      }
    }

    return dates;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (selectedMedications.length === 0) {
      alert('Выберите хотя бы одно лекарство');
      return;
    }

    const dates = getDatesForSchedule();
    if (dates.length === 0) {
      alert('Выберите дату или период');
      return;
    }

    try {
      // Генерируем seriesId для серии приемов (если больше одного приема)
      const seriesId = dates.length > 1 ? crypto.randomUUID() : undefined;

      console.log(`Creating ${dates.length} intakes for period`);

      // Создаем приемы последовательно для надежности
      for (const date of dates) {
        const medicationDoses: MedicationDose[] = selectedMedications.map(m => {
          const medication = (medications || []).find(med => med.id === m.medicationId);
          return {
            medicationId: m.medicationId,
            amount: Number(m.amount),
            unit: medication ? getUnitByForm(medication.form) : 'таблетки',
            confirmed: false,
          };
        });

        try {
          await dispatch(
            createIntake({
              dateTime: date.getTime(),
              medications: medicationDoses,
              seriesId, // Одинаковый seriesId для всех приемов в серии
            })
          ).unwrap();
          console.log(`Created intake for date: ${date.toISOString()}`);
        } catch (error) {
          console.error(`Failed to create intake for date ${date.toISOString()}:`, error);
          throw error;
        }
      }

      onClose();
      resetForm();
    } catch (error) {
      console.error('Failed to create intakes:', error);
      alert('Ошибка при создании приемов');
    }
  };

  const resetForm = () => {
    setScheduleType('single');
    setSingleDate(initialDate ? initialDate.toISOString().split('T')[0] : '');
    setStartDate('');
    setEndDate('');
    setSelectedWeekdays([]);
    setTime('09:00');
    setSelectedMedications([]);
  };

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <h2 className={styles.title}>Добавить прием</h2>
          <button onClick={onClose} className={styles.closeButton}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.scheduleType}>
            <label className={styles.label}>Тип расписания:</label>
            <div className={styles.radioGroup}>
              <label className={styles.radioLabel}>
                <input
                  type="radio"
                  value="single"
                  checked={scheduleType === 'single'}
                  onChange={e => setScheduleType(e.target.value as ScheduleType)}
                />
                Одна дата
              </label>
              <label className={styles.radioLabel}>
                <input
                  type="radio"
                  value="period"
                  checked={scheduleType === 'period'}
                  onChange={e => setScheduleType(e.target.value as ScheduleType)}
                />
                Период
              </label>
              <label className={styles.radioLabel}>
                <input
                  type="radio"
                  value="weekdays"
                  checked={scheduleType === 'weekdays'}
                  onChange={e => setScheduleType(e.target.value as ScheduleType)}
                />
                По дням недели
              </label>
            </div>
          </div>

          {scheduleType === 'single' && (
            <Input
              label="Дата"
              type="date"
              value={singleDate}
              onChange={e => setSingleDate(e.target.value)}
              required
            />
          )}

          {(scheduleType === 'period' || scheduleType === 'weekdays') && (
            <>
              <Input
                label="Начало периода"
                type="date"
                value={startDate}
                onChange={e => setStartDate(e.target.value)}
                required
              />
              <Input
                label="Конец периода"
                type="date"
                value={endDate}
                onChange={e => setEndDate(e.target.value)}
                required
              />
            </>
          )}

          {scheduleType === 'weekdays' && (
            <div className={styles.weekdays}>
              <label className={styles.label}>Дни недели:</label>
              <div className={styles.weekdaysList}>
                {weekdays.map(day => (
                  <button
                    key={day.value}
                    type="button"
                    onClick={() => toggleWeekday(day.value)}
                    className={cn(styles.weekdayButton, {
                      [styles.selected]: selectedWeekdays.includes(day.value),
                    })}
                  >
                    {day.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          <Input
            label="Время приема"
            type="time"
            value={time}
            onChange={e => setTime(e.target.value)}
            required
          />

          <div className={styles.medications}>
            <label className={styles.label}>Выберите лекарства:</label>
            <div className={styles.medicationFilters}>
              <Input
                label="Поиск по названию"
                placeholder="Введите название..."
                value={medicationNameFilter}
                onChange={e => setMedicationNameFilter(e.target.value)}
                onClear={() => setMedicationNameFilter('')}
              />
              <Select
                label="Фильтр по типу"
                value={medicationTypeFilter}
                onChange={value => setMedicationTypeFilter(value as MedicationForm | 'all')}
                options={[
                  { value: 'all', label: 'Все типы' },
                  ...medicationForms.map(form => ({ value: form, label: form })),
                ]}
              />
            </div>
            <div className={styles.medicationsList}>
              {filteredMedications.length === 0 ? (
                <div className={styles.empty}>
                  {(medications || []).length === 0
                    ? 'Нет доступных лекарств'
                    : 'Ничего не найдено'}
                </div>
              ) : (
                filteredMedications.map(medication => {
                  const selected = selectedMedications.find(m => m.medicationId === medication.id);
                  return (
                    <div key={medication.id} className={styles.medicationItem}>
                      <label className={styles.medicationCheckbox}>
                        <input
                          type="checkbox"
                          checked={!!selected}
                          onChange={() => toggleMedication(medication.id)}
                        />
                        <div className={styles.medicationImage}>
                          {medication.imageUrl ? (
                            <img src={medication.imageUrl} alt={medication.name} />
                          ) : (
                            <div className={styles.medicationIcon}>
                              {getMedicationIcon(medication.form)}
                            </div>
                          )}
                        </div>
                        <div className={styles.medicationInfo}>
                          <div className={styles.medicationName}>{medication.name}</div>
                          <div className={styles.medicationForm}>{medication.form}</div>
                        </div>
                      </label>
                      {selected && (
                        <div className={styles.doseInputs}>
                          <div className={styles.doseInputWrapper}>
                            <Input
                              type="number"
                              value={selected.amount}
                              onChange={e => updateMedicationAmount(medication.id, e.target.value)}
                              min="1"
                            />
                          </div>
                          <div className={styles.doseUnit}>{getUnitByForm(medication.form)}</div>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>

          <div className={styles.actions}>
            <Button type="button" variant="secondary" onClick={onClose}>
              Отмена
            </Button>
            <Button type="submit">Сохранить</Button>
          </div>
        </form>
      </div>
    </div>
  );
};
