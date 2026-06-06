import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { usersApi } from '../../api/users';
import type { UserPublicResponse } from '../../api/users';
import { attachAsGuardian } from '../../store/slices/guardiansSlice';
import { Button } from '../../components/Button/Button';
import { Input } from '../../components/Input/Input';
import {
  validateEmail,
  validateRelationship,
  hasErrors,
  type ValidationError,
} from '../../utils/validation';
import styles from './GuardiansAttachPage.module.scss';

type Notification = { type: 'success' | 'error'; message: string } | null;

export const GuardiansAttachPage = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const currentUser = useAppSelector(state => state.auth.user);

  const [email, setEmail] = useState('');
  const [relationship, setRelationship] = useState('Опекун');
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<Notification>(null);
  const [success, setSuccess] = useState(false);
  const [addedUser, setAddedUser] = useState<UserPublicResponse | null>(null);
  const [errors, setErrors] = useState<{
    email?: ValidationError;
    relationship?: ValidationError;
  }>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setNotification(null);
    const fieldErrors = {
      email: validateEmail(email),
      relationship: validateRelationship(relationship),
    };
    setErrors(fieldErrors);
    if (hasErrors(fieldErrors)) return;

    const trimmedEmail = email.trim().toLowerCase();
    if (currentUser?.email && trimmedEmail === currentUser.email.toLowerCase()) {
      setNotification({
        type: 'error',
        message:
          'Нельзя стать опекуном самого себя. Введите email человека, за которым вы хотите следить.',
      });
      return;
    }
    setLoading(true);
    try {
      const user = await usersApi.getByEmail(trimmedEmail);
      setAddedUser(user);
      const invite = await dispatch(
        attachAsGuardian({
          patientUserId: user.id,
          data: { relationship: relationship.trim() || null },
        })
      ).unwrap();
      setSuccess(true);
      setNotification({
        type: 'success',
        message:
          invite?.message ||
          'Запрос отправлен. Вы и подопечный должны подтвердить его в Telegram (@p111boxbot).',
      });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Не удалось привязаться как опекун. Возможно, пользователь с таким email не найден.';
      setNotification({ type: 'error', message });
    } finally {
      setLoading(false);
    }
  };

  const dismissNotification = () => setNotification(null);

  if (success) {
    return (
      <div className={styles.page}>
        <h1 className={styles.title}>Запрос отправлен</h1>
        <p className={styles.message}>
          Подтвердите в Telegram (@p111boxbot), что готовы стать опекуном. Связь установится,
          когда подтвердите и вы, и подопечный.
        </p>
        {addedUser && (
          <div className={styles.addedUserCard}>
            <div className={styles.addedUserName}>{addedUser.name}</div>
            <div className={styles.addedUserEmail}>{addedUser.email}</div>
          </div>
        )}
        {notification && (
          <div
            className={
              notification.type === 'success' ? styles.notificationSuccess : styles.notificationError
            }
          >
            {notification.message}
            <button type="button" onClick={dismissNotification} className={styles.notificationClose}>
              ×
            </button>
          </div>
        )}
        <Button onClick={() => navigate('/caregivers')}>К списку опекунов</Button>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Стать опекуном</h1>
      <p className={styles.message}>
        Введите email <strong>подопечного</strong>. После отправки подопечный получит запрос в
        Telegram (@p111boxbot) и должен подтвердить его. У подопечного должен быть привязан
        Telegram.
      </p>

      {notification && (
        <div
          className={
            notification.type === 'success' ? styles.notificationSuccess : styles.notificationError
          }
        >
          {notification.message}
          <button type="button" onClick={dismissNotification} className={styles.notificationClose}>
            ×
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit} className={styles.form} noValidate>
        <Input
          label="Email пользователя"
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="example@mail.ru"
          error={errors.email}
        />
        <Input
          label="Степень родства / роль (необязательно)"
          value={relationship}
          onChange={e => setRelationship(e.target.value)}
          error={errors.relationship}
        />
        <Button type="submit" disabled={loading}>
          {loading ? 'Отправка…' : 'Стать опекуном'}
        </Button>
      </form>

      <Button variant="secondary" onClick={() => navigate('/caregivers')} className={styles.back}>
        Отмена
      </Button>
    </div>
  );
};
