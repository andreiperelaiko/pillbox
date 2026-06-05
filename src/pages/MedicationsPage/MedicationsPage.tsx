import { useState } from 'react';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { createMedication } from '../../store/slices/medicationsSlice';
import { MedicationCard } from '../../components/MedicationCard/MedicationCard';
import { Button } from '../../components/Button/Button';
import { Input } from '../../components/Input/Input';
import {
  validateMedicationName,
  validateDescription,
  hasErrors,
  type ValidationError,
} from '../../utils/validation';
import styles from './MedicationsPage.module.scss';

export const MedicationsPage = () => {
  const dispatch = useAppDispatch();
  const { items: medications } = useAppSelector(state => state.medications);
  const [showForm, setShowForm] = useState(false);
  const [nameFilter, setNameFilter] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });
  const [errors, setErrors] = useState<{
    name?: ValidationError;
    description?: ValidationError;
  }>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    const fieldErrors = {
      name: validateMedicationName(formData.name),
      description: validateDescription(formData.description),
    };
    setErrors(fieldErrors);
    if (hasErrors(fieldErrors)) return;

    try {
      await dispatch(
        createMedication({
          name: formData.name.trim(),
          description: formData.description.trim() || null,
        })
      ).unwrap();
      setFormData({ name: '', description: '' });
      setErrors({});
      setShowForm(false);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Не удалось добавить лекарство.');
    }
  };

  const filteredMedications = (medications || []).filter(medication =>
    medication.name.toLowerCase().includes(nameFilter.toLowerCase())
  );

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Медикаменты</h1>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? 'Отмена' : '+ Добавить'}</Button>
      </div>

      <div className={styles.filters}>
        <Input
          label="Поиск по названию"
          placeholder="Введите название..."
          value={nameFilter}
          onChange={e => setNameFilter(e.target.value)}
          onClear={() => setNameFilter('')}
        />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className={styles.form} noValidate>
          <Input
            label="Название"
            value={formData.name}
            onChange={e => setFormData({ ...formData, name: e.target.value })}
            placeholder="Парацетамол"
            error={errors.name}
          />
          <Input
            label="Описание"
            value={formData.description}
            onChange={e => setFormData({ ...formData, description: e.target.value })}
            placeholder="Жаропонижающее и обезболивающее, 500мг"
            error={errors.description}
          />
          {submitError && <div className={styles.submitError}>{submitError}</div>}
          <Button type="submit">Сохранить</Button>
        </form>
      )}

      <div className={styles.list}>
        {filteredMedications.length === 0 ? (
          <div className={styles.empty}>
            {(medications || []).length === 0 ? 'Нет медикаментов' : 'Ничего не найдено'}
          </div>
        ) : (
          filteredMedications.map(medication => (
            <MedicationCard key={medication.id} medication={medication} />
          ))
        )}
      </div>
    </div>
  );
};
