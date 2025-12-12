import { useState } from 'react';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { createMedication, deleteMedication } from '../../store/slices/medicationsSlice';
import { MedicationCard } from '../../components/MedicationCard/MedicationCard';
import { Button } from '../../components/Button/Button';
import { Input } from '../../components/Input/Input';
import { Select } from '../../components/Select/Select';
import type { MedicationForm } from '../../types';
import styles from './MedicationsPage.module.scss';

const medicationForms: MedicationForm[] = [
  'таблетки',
  'капсулы',
  'жидкость',
  'укол',
  'порошок',
  'мазь',
  'спрей',
];

export const MedicationsPage = () => {
  const dispatch = useAppDispatch();
  const { items: medications } = useAppSelector(state => state.medications);
  const [showForm, setShowForm] = useState(false);
  const [nameFilter, setNameFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState<MedicationForm | 'all'>('all');
  const [formData, setFormData] = useState({
    name: '',
    form: 'таблетки' as MedicationForm,
    defaultAmount: '1',
    imageUrl: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await dispatch(
      createMedication({
        name: formData.name,
        form: formData.form,
        defaultAmount: Number(formData.defaultAmount),
        imageUrl: formData.imageUrl || null,
      })
    ).unwrap();
    setFormData({
      name: '',
      form: 'таблетки',
      defaultAmount: '1',
      imageUrl: '',
    });
    setShowForm(false);
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = event => {
        setFormData({ ...formData, imageUrl: event.target?.result as string });
      };
      reader.readAsDataURL(file);
    }
  };

  const filteredMedications = (medications || []).filter(medication => {
    const matchesName = medication.name.toLowerCase().includes(nameFilter.toLowerCase());
    const matchesType = typeFilter === 'all' || medication.form === typeFilter;
    return matchesName && matchesType;
  });

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
        <Select
          label="Фильтр по типу"
          value={typeFilter}
          onChange={value => setTypeFilter(value as MedicationForm | 'all')}
          options={[
            { value: 'all', label: 'Все типы' },
            ...medicationForms.map(form => ({ value: form, label: form })),
          ]}
        />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className={styles.form}>
          <Input
            label="Название"
            value={formData.name}
            onChange={e => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <Select
            label="Форма"
            value={formData.form}
            onChange={value => setFormData({ ...formData, form: value as MedicationForm })}
            options={medicationForms.map(form => ({ value: form, label: form }))}
          />
          <Input
            label="Количество по умолчанию"
            type="number"
            value={formData.defaultAmount}
            onChange={e => setFormData({ ...formData, defaultAmount: e.target.value })}
            required
            min="1"
          />
          <div className={styles.imageInput}>
            <label className={styles.label}>Фотография (опционально)</label>
            <input type="file" accept="image/*" onChange={handleImageChange} />
            {formData.imageUrl && (
              <img src={formData.imageUrl} alt="Preview" className={styles.preview} />
            )}
          </div>
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
            <MedicationCard
              key={medication.id}
              medication={medication}
              onDelete={() => dispatch(deleteMedication(medication.id)).unwrap()}
            />
          ))
        )}
      </div>
    </div>
  );
};
