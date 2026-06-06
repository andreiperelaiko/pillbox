import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { logoutUser, logoutAllUser, fetchMe } from '../../store/slices/authSlice';
import { setTheme } from '../../store/slices/settingsSlice';
import { applyTheme } from '../../components/ThemeApplier/ThemeApplier';
import type { AppTheme } from '../../types';
import { settingsApi, type AccountSettings } from '../../api/settings';
import { Button } from '../../components/Button/Button';
import { Input } from '../../components/Input/Input';
import { validateTelegram } from '../../utils/validation';
import styles from './SettingsPage.module.scss';

export const SettingsPage = () => {
  const dispatch = useAppDispatch();
  const user = useAppSelector(state => state.auth.user);
  const theme = useAppSelector(state => state.settings.theme);
  const [searchParams, setSearchParams] = useSearchParams();

  const [account, setAccount] = useState<AccountSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [telegramInput, setTelegramInput] = useState('');
  const [telegramError, setTelegramError] = useState<string | undefined>();
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [emailSending, setEmailSending] = useState(false);
  const [telegramSaving, setTelegramSaving] = useState(false);

  const loadAccount = useCallback(async () => {
    setLoading(true);
    try {
      const data = await settingsApi.getAccount();
      setAccount(data);
      setTelegramInput(data.telegram ? `@${data.telegram.replace(/^@/, '')}` : '');
    } catch {
      setActionError('Не удалось загрузить настройки.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAccount();
  }, [loadAccount]);

  useEffect(() => {
    const refresh = () => {
      if (document.visibilityState === 'visible') {
        loadAccount();
      }
    };
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', refresh);
    return () => {
      window.removeEventListener('focus', refresh);
      document.removeEventListener('visibilitychange', refresh);
    };
  }, [loadAccount]);

  useEffect(() => {
    const emailVerified = searchParams.get('email_verified');
    if (emailVerified === '1') {
      setActionMessage('Email успешно подтверждён.');
      dispatch(fetchMe());
      loadAccount();
      setSearchParams({}, { replace: true });
    } else if (emailVerified === '0') {
      setActionError('Ссылка подтверждения email недействительна или устарела.');
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams, dispatch, loadAccount]);

  const handleSendEmailVerification = async () => {
    setEmailSending(true);
    setActionError(null);
    setActionMessage(null);
    try {
      const res = await settingsApi.sendEmailVerification();
      if (res.message === 'Email already verified') {
        setActionMessage('Email уже подтверждён.');
        await loadAccount();
      } else {
        setActionMessage(
          'Письмо с ссылкой отправлено. Проверьте почту и папку «Спам». ' +
            'Если письма нет — на сервере может быть не настроен исходящий SMTP.'
        );
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Не удалось отправить письмо.');
    } finally {
      setEmailSending(false);
    }
  };

  const handleSaveTelegram = async () => {
    const err = validateTelegram(telegramInput);
    setTelegramError(err ?? undefined);
    if (err) return;

    setTelegramSaving(true);
    setActionError(null);
    setActionMessage(null);
    try {
      await settingsApi.updateTelegram(telegramInput.trim());
      await dispatch(fetchMe()).unwrap();
      await loadAccount();
      setActionMessage('Telegram username сохранён. Откройте бота и нажмите Start.');
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Не удалось сохранить Telegram.');
    } finally {
      setTelegramSaving(false);
    }
  };

  const handleLogout = () => {
    dispatch(logoutUser());
  };

  const handleLogoutAll = () => {
    dispatch(logoutAllUser());
  };

  const displayEmail = account?.email ?? user?.email ?? '';

  const handleThemeChange = (next: AppTheme) => {
    dispatch(setTheme(next));
    applyTheme(next);
  };

  const themeOptions: { value: AppTheme; label: string; hint: string }[] = [
    { value: 'light', label: 'Светлая', hint: 'Стандартный вид' },
    { value: 'dark', label: 'Тёмная', hint: 'Меньше яркости, удобно вечером' },
    { value: 'accessible', label: 'Для слабовидящих', hint: 'Крупный текст и высокий контраст' },
  ];

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Настройки</h1>

      {actionMessage && <div className={styles.success}>{actionMessage}</div>}
      {actionError && <div className={styles.error}>{actionError}</div>}

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Оформление</h2>
        <p className={styles.hint}>Тема сохраняется в этом браузере.</p>
        <div className={styles.themeGrid} role="radiogroup" aria-label="Тема оформления">
          {themeOptions.map(option => (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={theme === option.value}
              className={
                theme === option.value ? styles.themeCardActive : styles.themeCard
              }
              onClick={() => handleThemeChange(option.value)}
            >
              <span className={styles.themeLabel}>{option.label}</span>
              <span className={styles.themeHint}>{option.hint}</span>
            </button>
          ))}
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Подтверждение контактов</h2>
        <p className={styles.hint}>
          Уведомления о пропущенных приёмах приходят на почту и в Telegram. Подтвердите оба канала.
        </p>

        {loading ? (
          <p className={styles.hint}>Загрузка…</p>
        ) : (
          <>
            <div className={styles.verifyRow}>
              <div className={styles.verifyInfo}>
                <div className={styles.verifyLabel}>Email</div>
                <div className={styles.verifyValue}>{displayEmail}</div>
                <span
                  className={
                    account?.email_verified ? styles.badgeVerified : styles.badgePending
                  }
                >
                  {account?.email_verified ? 'Подтверждён' : 'Не подтверждён'}
                </span>
              </div>
              {!account?.email_verified && (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleSendEmailVerification}
                  disabled={emailSending}
                >
                  {emailSending ? 'Отправка…' : 'Отправить письмо'}
                </Button>
              )}
            </div>

            <div className={styles.verifyRow}>
              <div className={styles.verifyInfo}>
                <div className={styles.verifyLabel}>Telegram</div>
                <div className={styles.verifyValue}>
                  {account?.telegram ? `@${account.telegram.replace(/^@/, '')}` : 'Не указан'}
                </div>
                <span
                  className={
                    account?.telegram_verified ? styles.badgeVerified : styles.badgePending
                  }
                >
                  {account?.telegram_verified ? 'Подтверждён' : 'Не подтверждён'}
                </span>
              </div>
              {account && !account.telegram_verified && account.telegram_bot_url && (
                <a
                  href={account.telegram_bot_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.externalLink}
                >
                  Открыть бота
                </a>
              )}
            </div>

            {!account?.telegram_verified && (
              <div className={styles.form}>
                <Input
                  label="Telegram username"
                  value={telegramInput}
                  onChange={e => setTelegramInput(e.target.value)}
                  placeholder="@username"
                  error={telegramError}
                />
                <p className={styles.hint}>
                  Username должен совпадать с аккаунтом в Telegram. После сохранения откройте бота
                  и нажмите <strong>Start</strong>.
                </p>
                <Button
                  type="button"
                  onClick={handleSaveTelegram}
                  disabled={telegramSaving}
                >
                  {telegramSaving ? 'Сохранение…' : 'Сохранить username'}
                </Button>
              </div>
            )}

            {account?.telegram_verified && (
              <Button type="button" variant="secondary" onClick={loadAccount}>
                Обновить статус
              </Button>
            )}
          </>
        )}
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Аккаунт</h2>
        <Button type="button" variant="danger" onClick={handleLogout}>
          Выйти из аккаунта
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={handleLogoutAll}
          className={styles.logoutAllButton}
        >
          Выйти из всех аккаунтов
        </Button>
      </section>
    </div>
  );
};
