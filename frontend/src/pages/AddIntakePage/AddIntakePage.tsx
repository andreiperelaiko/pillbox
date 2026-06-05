import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { createSchedule } from '../../store/slices/schedulesSlice';
import { Button } from '../../components/Button/Button';
import { Input } from '../../components/Input/Input';
import { getMedicationIcon } from '../../utils/medicationIcons';
import { formatDateLocal } from '../../utils/dateUtils';
import {
  validateDate,
  validateDateRange,
  validateTime,
  validateDose,
  type ValidationError,
} from '../../utils/validation';
import styles from './AddIntakePage.module.scss';
import cn from 'classnames';

type ScheduleType = 'single' | 'period' | 'weekdays';

interface IntakeErrors {
  singleDate?: ValidationError;
  startDate?: ValidationError;
  endDate?: ValidationError;
  weekdays?: ValidationError;
  time?: ValidationError;
  medications?: ValidationError;
  doses?: ValidationError;
}

export const AddIntakePage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { items: medications } = useAppSelector(state => state.medications);

  const dateParam = searchParams.get('date');
  const initialDate = dateParam
    ? (() => {
        const [y, m, d] = dateParam.split('-').map(Number);
        if (y && m && d) return new Date(y, m - 1, d);
        return null;
      })()
    : null;

  const [scheduleType, setScheduleType] = useState<ScheduleType>('single');
  const [singleDate, setSingleDate] = useState(
    initialDate ? formatDateLocal(initialDate) : ''
  );
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedWeekdays, setSelectedWeekdays] = useState<number[]>([]);
  const [time, setTime] = useState('09:00');
  const [selectedMedications, setSelectedMedications] = useState<
    Array<{ medicationId: string; amount: string }>
  >([]);
  const [medicationNameFilter, setMedicationNameFilter] = useState('');
  const [errors, setErrors] = useState<IntakeErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (initialDate) setSingleDate(formatDateLocal(initialDate));
  }, [initialDate]);

  const weekdays = [
    { value: 1, label: 'Пн' },
    { value: 2, label: 'Вт' },
    { value: 3, label: 'Ср' },
    { value: 4, label: 'Чт' },
    { value: 5, label: 'Пт' },
    { value: 6, label: 'Сб' },
    { value: 0, label: 'Вс' },
  ];

  const filteredMedications = (medications || []).filter(medication =>
    medication.name.toLowerCase().includes(medicationNameFilter.toLowerCase())
  );

  const toggleMedication = (medicationId: string) => {
    const medication = (medications || []).find(m => m.id === medicationId);
    if (!medication) return;
    const existing = selectedMedications.find(m => m.medicationId === medicationId);
    if (existing) {
      setSelectedMedications(selectedMedications.filter(m => m.medicationId !== medicationId));
    } else {
      setSelectedMedications([
        ...selectedMedications,
        { medicationId, amount: '' },
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
        const [year, month, day] = singleDate.split('-').map(Number);
        dates.push(new Date(year, month - 1, day, hours, minutes, 0, 0));
      }
    } else if (scheduleType === 'period' && startDate && endDate) {
      const [startYear, startMonth, startDay] = startDate.split('-').map(Number);
      const [endYear, endMonth, endDay] = endDate.split('-').map(Number);
      const start = new Date(startYear, startMonth - 1, startDay);
      const end = new Date(endYear, endMonth - 1, endDay);
      start.setHours(0, 0, 0, 0);
      end.setHours(0, 0, 0, 0);
      const current = new Date(start);
      while (current.getTime() <= end.getTime()) {
        const date = new Date(current);
        date.setHours(hours, minutes, 0, 0);
        dates.push(date);
        current.setDate(current.getDate() + 1);
      }
    } else if (scheduleType === 'weekdays' && selectedWeekdays.length > 0 && startDate && endDate) {
      const [startYear, startMonth, startDay] = startDate.split('-').map(Number);
      const [endYear, endMonth, endDay] = endDate.split('-').map(Number);
      const start = new Date(startYear, startMonth - 1, startDay, 0, 0, 0, 0);
      const end = new Date(endYear, endMonth - 1, endDay, 23, 59, 59, 999);
      const current = new Date(start);
      while (current <= end) {
        if (selectedWeekdays.includes(current.getDay())) {
          const date = new Date(current);
          date.setHours(hours, minutes, 0, 0);
          dates.push(date);
        }
        current.setDate(current.getDate() + 1);
      }
    }
    return dates;
  };

  /** Проверяет поля формы и возвращает карту ошибок (для текущего типа расписания). */
  const validateForm = (): IntakeErrors => {
    const next: IntakeErrors = {};

    if (scheduleType === 'single') {
      next.singleDate = validateDate(singleDate);
    } else {
      const rangeErr = validateDateRange(startDate, endDate);
      if (rangeErr) {
        // Привязываем ошибку к соответствующему полю для наглядности.
        const startErr = validateDate(startDate, 'дату начала');
        if (startErr) next.startDate = startErr;
        else next.endDate = rangeErr;
      }
      if (scheduleType === 'weekdays' && selectedWeekdays.length === 0) {
        next.weekdays = 'Выберите хотя бы один день недели.';
      }
    }

    next.time = validateTime(time);

    if (selectedMedications.length === 0) {
      next.medications = 'Выберите хотя бы одно лекарство.';
    } else {
      const doseErr = selectedMedications
        .map(m => validateDose(m.amount))
        .find((err): err is string => Boolean(err));
      if (doseErr) next.doses = doseErr;
    }

    return next;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    const fieldErrors = validateForm();
    setErrors(fieldErrors);
    if (Object.values(fieldErrors).some(Boolean)) return;

    const dates = getDatesForSchedule();
    if (dates.length === 0) {
      setSubmitError('Не удалось определить даты приёма. Проверьте расписание.');
      return;
    }
    try {
      for (const date of dates) {
        for (const sel of selectedMedications) {
          await dispatch(
            createSchedule({
              medication_id: Number(sel.medicationId),
              intake_at: date.toISOString(),
              dose: sel.amount.trim() || null,
            })
          ).unwrap();
        }
      }
      navigate(-1);
    } catch (error) {
      console.error('Failed to create intakes:', error);
      setSubmitError(
        error instanceof Error ? error.message : 'Ошибка при создании приёмов.'
      );
    }
  };

  const handleCancel = () => navigate(-1);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Добавить прием</h1>
        <Button type="button" variant="secondary" onClick={handleCancel} className={styles.back}>
          Отмена
        </Button>
      </div>

      <form onSubmit={handleSubmit} className={styles.form} noValidate>
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
            error={errors.singleDate}
          />
        )}

        {(scheduleType === 'period' || scheduleType === 'weekdays') && (
          <>
            <Input
              label="Начало периода"
              type="date"
              value={startDate}
              onChange={e => setStartDate(e.target.value)}
              error={errors.startDate}
            />
            <Input
              label="Конец периода"
              type="date"
              value={endDate}
              onChange={e => setEndDate(e.target.value)}
              error={errors.endDate}
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
            {errors.weekdays && <span className={styles.fieldError}>{errors.weekdays}</span>}
          </div>
        )}

        <Input
          label="Время приема"
          type="time"
          value={time}
          onChange={e => setTime(e.target.value)}
          error={errors.time}
        />

        <div className={styles.medications}>
          <label className={styles.label}>Выберите лекарства:</label>
          {errors.medications && (
            <span className={styles.fieldError}>{errors.medications}</span>
          )}
          <div className={styles.medicationFilters}>
            <Input
              label="Поиск по названию"
              placeholder="Введите название..."
              value={medicationNameFilter}
              onChange={e => setMedicationNameFilter(e.target.value)}
              onClear={() => setMedicationNameFilter('')}
            />
          </div>
          <div className={styles.medicationsList}>
            {filteredMedications.length === 0 ? (
              <div className={styles.empty}>
                {(medications || []).length === 0 ? 'Нет доступных лекарств' : 'Ничего не найдено'}
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
                            {getMedicationIcon('таблетки')}
                          </div>
                        )}
                      </div>
                      <div className={styles.medicationInfo}>
                        <div className={styles.medicationName}>{medication.name}</div>
                        <div className={styles.medicationForm}>
                          {medication.description ?? '—'}
                        </div>
                      </div>
                    </label>
                    {selected && (
                      <div className={styles.doseInputs}>
                        <Input
                          type="text"
                          value={selected.amount}
                          onChange={e => updateMedicationAmount(medication.id, e.target.value)}
                          placeholder="Дозировка, например: 1 таблетка, 5 мл"
                          error={validateDose(selected.amount)}
                        />
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {submitError && <div className={styles.submitError}>{submitError}</div>}

        <div className={styles.actions}>
          <Button type="button" variant="secondary" onClick={handleCancel}>
            Отмена
          </Button>
          <Button type="submit">Сохранить</Button>
        </div>
      </form>
    </div>
  );
};
