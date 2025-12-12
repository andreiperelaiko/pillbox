import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { updateSettings } from '../../store/slices/settingsSlice';
import { Button } from '../../components/Button/Button';
import { Input } from '../../components/Input/Input';
import { useEffect, useState } from 'react';
import styles from './SettingsPage.module.scss';

export const SettingsPage = () => {
  const dispatch = useAppDispatch();

  const settings = useAppSelector(state => state.settings);

  const [delayMinutes, setDelayMinutes] = useState(settings.notificationDelayMinutes.toString());

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await dispatch(updateSettings({ notificationDelayMinutes: Number(delayMinutes) })).unwrap();
      alert('Настройки сохранены');
    } catch (error) {
      console.error('Failed to update settings:', error);

      alert('Ошибка при сохранении настроек');
    }
  };

  useEffect(() => {
    setDelayMinutes(settings.notificationDelayMinutes.toString());
  }, [settings.notificationDelayMinutes]);

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Настройки</h1>

      <form onSubmit={handleSubmit} className={styles.form}>
        <Input
          label="Задержка уведомлений (минуты)"
          type="number"
          value={delayMinutes}
          onChange={e => setDelayMinutes(e.target.value)}
          min="1"
          required
        />
        <p className={styles.hint}>
          Если прием просрочен на указанное количество минут, опекунам будет отправлено уведомление
        </p>
        <Button type="submit">Сохранить</Button>
      </form>
    </div>
  );
};
