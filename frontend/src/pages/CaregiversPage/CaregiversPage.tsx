import { useState } from 'react';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { createCaregiver, deleteCaregiver } from '../../store/slices/caregiversSlice';
import { Button } from '../../components/Button/Button';
import { Input } from '../../components/Input/Input';
import styles from './CaregiversPage.module.scss';

export const CaregiversPage = () => {
  const dispatch = useAppDispatch();
  const { items: caregivers } = useAppSelector(state => state.caregivers);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    telegram: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await dispatch(createCaregiver(formData)).unwrap();
    setFormData({ name: '', phone: '', email: '', telegram: '' });
    setShowForm(false);
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Опекуны</h1>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? 'Отмена' : '+ Добавить'}</Button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className={styles.form}>
          <Input
            label="Имя"
            value={formData.name}
            onChange={e => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <Input
            label="Телефон"
            type="tel"
            value={formData.phone}
            onChange={e => setFormData({ ...formData, phone: e.target.value })}
            required
          />
          <Input
            label="Email"
            type="email"
            value={formData.email}
            onChange={e => setFormData({ ...formData, email: e.target.value })}
            required
          />
          <Input
            label="Ник телеграм"
            placeholder="@username"
            value={formData.telegram}
            onChange={e => setFormData({ ...formData, telegram: e.target.value })}
            onClear={() => setFormData({ ...formData, telegram: '' })}
            required
          />
          <Button type="submit">Сохранить</Button>
        </form>
      )}

      <div className={styles.list}>
        {(caregivers || []).length === 0 ? (
          <div className={styles.empty}>Нет опекунов</div>
        ) : (
          (caregivers || []).map(caregiver => (
            <div key={caregiver.id} className={styles.card}>
              <div className={styles.info}>
                <div className={styles.name}>{caregiver.name}</div>
                <div className={styles.contact}>{caregiver.phone}</div>
                <div className={styles.contact}>{caregiver.email}</div>
                {caregiver.telegram && (
                  <div className={styles.contact}>Telegram: {caregiver.telegram}</div>
                )}
              </div>
              <Button
                variant="danger"
                onClick={() => dispatch(deleteCaregiver(caregiver.id)).unwrap()}
              >
                Удалить
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
