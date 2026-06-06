import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { guardiansApi } from '../../api/guardians';
import { Button } from '../../components/Button/Button';
import { Input } from '../../components/Input/Input';
import {
  validateEmail,
  validateRelationship,
  hasErrors,
  type ValidationError,
} from '../../utils/validation';
import { toUserFriendlyError } from '../../utils/errorMessages';
import { ApiError } from '../../api/base';
import styles from '../GuardiansAttachPage/GuardiansAttachPage.module.scss';

export const GuardianInvitePage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [relationship, setRelationship] = useState('Опекун');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errors, setErrors] = useState<{
    email?: ValidationError;
    relationship?: ValidationError;
  }>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    const fieldErrors = {
      email: validateEmail(email),
      relationship: validateRelationship(relationship),
    };
    setErrors(fieldErrors);
    if (hasErrors(fieldErrors)) return;

    setLoading(true);
    try {
      const res = await guardiansApi.inviteByEmail({
        email: email.trim(),
        relationship: relationship.trim() || null,
      });
      setMessage(res.message);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(toUserFriendlyError(err.message, err.status));
      } else {
        setError(err instanceof Error ? err.message : 'Не удалось отправить приглашение.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Пригласить опекуна</h1>
      <p className={styles.message}>
        Введите email опекуна. Опекун получит запрос в боте <strong>@p111boxbot</strong> и должен
        подтвердить его. У опекуна должен быть привязан Telegram в настройках.
      </p>

      {message && <div className={styles.notificationSuccess}>{message}</div>}
      {error && <div className={styles.notificationError}>{error}</div>}

      <form onSubmit={handleSubmit} className={styles.form} noValidate>
        <Input
          label="Email опекуна"
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="opекун@mail.ru"
          error={errors.email}
        />
        <Input
          label="Степень родства / роль"
          value={relationship}
          onChange={e => setRelationship(e.target.value)}
          error={errors.relationship}
        />
        <Button type="submit" disabled={loading}>
          {loading ? 'Отправка…' : 'Отправить приглашение'}
        </Button>
      </form>

      <Button variant="secondary" onClick={() => navigate('/caregivers')} className={styles.back}>
        Назад
      </Button>
    </div>
  );
};
