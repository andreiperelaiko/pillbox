import { useState, useMemo } from 'react';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { createSchedule, markScheduleTaken } from '../../store/slices/schedulesSlice';
import { scheduleItemsToGroupedViews } from '../../utils/scheduleUtils';
import { IntakeCard } from '../../components/IntakeCard/IntakeCard';
import { Button } from '../../components/Button/Button';
import { Input } from '../../components/Input/Input';
import { Select } from '../../components/Select/Select';
import type { DosageUnit } from '../../types';
import styles from './IntakesPage.module.scss';

const dosageUnits: DosageUnit[] = ['таблетки', 'мл', 'мг', 'уколы', 'капсулы', 'г'];

export const IntakesPage = () => {
  const dispatch = useAppDispatch();
  const { items: medications } = useAppSelector(state => state.medications);
  const { items: scheduleItems } = useAppSelector(state => state.schedules);

  const groupedIntakes = useMemo(
    () => scheduleItemsToGroupedViews(scheduleItems || []),
    [scheduleItems]
  );

  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    date: '',
    time: '',
    selectedMedications: [] as Array<{
      medicationId: string;
      amount: string;
      unit: DosageUnit;
    }>,
  });

  const handleAddMedication = () => {
    setFormData({
      ...formData,
      selectedMedications: [
        ...formData.selectedMedications,
        { medicationId: medications[0]?.id || '', amount: '1', unit: 'таблетки' },
      ],
    });
  };

  const handleRemoveMedication = (index: number) => {
    setFormData({
      ...formData,
      selectedMedications: formData.selectedMedications.filter((_, i) => i !== index),
    });
  };

  const handleMedicationChange = (index: number, field: string, value: string) => {
    const updated = [...formData.selectedMedications];
    updated[index] = { ...updated[index], [field]: value };
    setFormData({ ...formData, selectedMedications: updated });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const date = new Date(`${formData.date}T${formData.time}`);
    for (const m of formData.selectedMedications) {
      const unit = 'шт.';
      await dispatch(
        createSchedule({
          medication_id: Number(m.medicationId),
          intake_at: date.toISOString(),
          dose: `${m.amount} ${unit}`,
        })
      ).unwrap();
    }
    setFormData({ date: '', time: '', selectedMedications: [] });
    setShowForm(false);
  };

  const handleConfirm = (scheduleId: number) => {
    dispatch(markScheduleTaken({ schedule_id: scheduleId }));
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Приемы медикаментов</h1>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Отмена' : '+ Добавить прием'}
        </Button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.dateTimeRow}>
            <Input
              label="Дата"
              type="date"
              value={formData.date}
              onChange={e => setFormData({ ...formData, date: e.target.value })}
              required
            />
            <Input
              label="Время"
              type="time"
              value={formData.time}
              onChange={e => setFormData({ ...formData, time: e.target.value })}
              required
            />
          </div>

          <div className={styles.medicationsSection}>
            <div className={styles.medicationsHeader}>
              <h3>Медикаменты</h3>
              <Button type="button" onClick={handleAddMedication} variant="secondary">
                + Добавить
              </Button>
            </div>

            {formData.selectedMedications.map((med, index) => (
              <div key={index} className={styles.medicationRow}>
                <Select
                  value={med.medicationId}
                  onChange={value => handleMedicationChange(index, 'medicationId', value)}
                  options={(medications || []).map(m => ({ value: m.id, label: m.name }))}
                />
                <Input
                  type="number"
                  value={med.amount}
                  onChange={e => handleMedicationChange(index, 'amount', e.target.value)}
                  min="1"
                />
                <Select
                  value={med.unit}
                  onChange={value => handleMedicationChange(index, 'unit', value)}
                  options={dosageUnits.map(u => ({ value: u, label: u }))}
                />
                <Button
                  type="button"
                  onClick={() => handleRemoveMedication(index)}
                  variant="danger"
                >
                  ×
                </Button>
              </div>
            ))}
          </div>

          <Button type="submit" disabled={formData.selectedMedications.length === 0}>
            Сохранить
          </Button>
        </form>
      )}

      <div className={styles.list}>
        {groupedIntakes.length === 0 ? (
          <div className={styles.empty}>Нет приемов</div>
        ) : (
          [...groupedIntakes]
            .sort((a, b) => b.dateTime - a.dateTime)
            .map(intake => (
              <IntakeCard
                key={intake.id}
                intake={intake}
                medications={medications || []}
                onConfirm={handleConfirm}
              />
            ))
        )}
      </div>
    </div>
  );
};
