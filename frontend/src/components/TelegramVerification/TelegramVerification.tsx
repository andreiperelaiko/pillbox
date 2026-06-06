import { useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { fetchMe } from '../../store/slices/authSlice';
import { Button } from '../Button/Button';
import styles from './TelegramVerification.module.scss';

/** @username бота для привязки. Задаётся через VITE_TELEGRAM_BOT_USERNAME. */
const BOT_USERNAME = (import.meta.env.VITE_TELEGRAM_BOT_USERNAME as string | undefined)?.replace(
  /^@/,
  ''
);

type CheckState = 'idle' | 'checking' | 'still-pending';

export const TelegramVerification = () => {
  const dispatch = useAppDispatch();
  const user = useAppSelector(state => state.auth.user);
  const [checkState, setCheckState] = useState<CheckState>('idle');

  const telegram = user?.telegram?.replace(/^@/, '');
  const isVerified = Boolean(user?.telegram_chat_id);
  const botLink = BOT_USERNAME ? `https://t.me/${BOT_USERNAME}` : null;

  const handleCheck = async () => {
    setCheckState('checking');
    try {
      const updated = await dispatch(fetchMe()).unwrap();
      setCheckState(updated?.telegram_chat_id ? 'idle' : 'still-pending');
    } catch {
      setCheckState('still-pending');
    }
  };

  return (
    <div className={styles.wrap}>
      <div className={styles.head}>
        <span className={styles.rowTitle}>Telegram</span>
        <span className={isVerified ? styles.badgeOk : styles.badgePending}>
          {isVerified ? '✓ Подтверждён' : 'Не подтверждён'}
        </span>
      </div>

      {isVerified ? (
        <p className={styles.hint}>
          Telegram {telegram ? <strong>@{telegram}</strong> : ''} привязан. Вы будете получать
          уведомления о приёмах.
        </p>
      ) : !telegram ? (
        <p className={styles.hint}>
          Telegram не был указан при регистрации, поэтому уведомления недоступны. Чтобы привязать
          его, зарегистрируйте аккаунт с указанием Telegram.
        </p>
      ) : (
        <>
          <p className={styles.hint}>
            Чтобы получать уведомления, подтвердите Telegram <strong>@{telegram}</strong>:
          </p>
          <ol className={styles.steps}>
            <li>
              Откройте бота{' '}
              {botLink ? (
                <a href={botLink} target="_blank" rel="noopener noreferrer">
                  @{BOT_USERNAME}
                </a>
              ) : (
                'таблетницы'
              )}
            </li>
            <li>
              Отправьте команду <code>/start</code>
            </li>
            <li>Нажмите «Проверить» ниже</li>
          </ol>

          <div className={styles.actions}>
            {botLink && (
              <a href={botLink} target="_blank" rel="noopener noreferrer">
                <Button type="button">Открыть бота</Button>
              </a>
            )}
            <Button
              type="button"
              variant="secondary"
              onClick={handleCheck}
              disabled={checkState === 'checking'}
            >
              {checkState === 'checking' ? 'Проверяем…' : 'Проверить'}
            </Button>
          </div>

          {checkState === 'still-pending' && (
            <p className={styles.pendingMsg}>
              Пока не привязано. Убедитесь, что отправили <code>/start</code> боту с того же
              Telegram-аккаунта (@{telegram}), и попробуйте снова.
            </p>
          )}
        </>
      )}
    </div>
  );
};
