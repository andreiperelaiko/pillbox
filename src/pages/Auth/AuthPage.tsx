import { FormEvent, useState } from 'react';
import cn from 'classnames';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { loginUser, registerUser } from '../../store/slices/authSlice';
import {
  validateEmail,
  validateLoginPassword,
  validateNewPassword,
  validateName,
  validateTelegram,
  hasErrors,
  type ValidationError,
} from '../../utils/validation';
import styles from './AuthPage.module.scss';

type Mode = 'login' | 'register';

interface FieldErrors {
  email?: ValidationError;
  password?: ValidationError;
  name?: ValidationError;
  telegram?: ValidationError;
}

export const AuthPage = () => {
  const dispatch = useAppDispatch();
  const { loading, error } = useAppSelector(state => state.auth);
  const [mode, setMode] = useState<Mode>('login');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [telegram, setTelegram] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  /** Проверяет все поля для текущего режима и возвращает карту ошибок. */
  const validate = (): FieldErrors => {
    if (mode === 'login') {
      return {
        email: validateEmail(email),
        password: validateLoginPassword(password),
      };
    }
    return {
      email: validateEmail(email),
      password: validateNewPassword(password),
      name: validateName(name),
      telegram: validateTelegram(telegram),
    };
  };

  const handleLogin = async () => {
    try {
      await dispatch(
        loginUser({ email: email.trim(), password, remember_me: rememberMe })
      ).unwrap();
    } catch {
      // error in state
    }
  };

  const handleRegister = async () => {
    try {
      await dispatch(
        registerUser({
          email: email.trim(),
          name: name.trim(),
          password,
          telegram: telegram.trim() || undefined,
        })
      ).unwrap();
    } catch {
      // error in state
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const errors = validate();
    setFieldErrors(errors);
    if (hasErrors(errors)) return;
    if (mode === 'login') handleLogin();
    else handleRegister();
  };

  const switchMode = (next: Mode) => {
    setMode(next);
    setFieldErrors({});
  };

  return (
    <div className={styles.wrap}>
      <div className={styles.card}>
        <header className={styles.header}>
          <h1 className={styles.title}>Таблетница</h1>
          <p className={styles.tagline}>Забота о самых близких</p>
        </header>

        <div className={styles.tabs}>
          <button
            type="button"
            className={cn(styles.tab, { [styles.active]: mode === 'login' })}
            onClick={() => switchMode('login')}
          >
            Вход
          </button>
          <button
            type="button"
            className={cn(styles.tab, { [styles.active]: mode === 'register' })}
            onClick={() => switchMode('register')}
          >
            Регистрация
          </button>
        </div>

        <form onSubmit={handleSubmit} className={styles.form} noValidate>
          {mode === 'register' && (
            <>
              <div className={styles.field}>
                <label htmlFor="name" className={styles.label}>
                  Имя
                </label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className={cn(styles.input, { [styles.inputError]: !!fieldErrors.name })}
                  placeholder="Иван Петров"
                  autoComplete="name"
                  aria-invalid={!!fieldErrors.name}
                />
                {fieldErrors.name && (
                  <span className={styles.fieldError}>{fieldErrors.name}</span>
                )}
              </div>
              <div className={styles.field}>
                <label htmlFor="telegram" className={styles.label}>
                  Telegram <span className={styles.optional}>(необязательно)</span>
                </label>
                <input
                  id="telegram"
                  type="text"
                  value={telegram}
                  onChange={e => setTelegram(e.target.value)}
                  className={cn(styles.input, { [styles.inputError]: !!fieldErrors.telegram })}
                  placeholder="@username"
                  autoComplete="off"
                  aria-invalid={!!fieldErrors.telegram}
                />
                {fieldErrors.telegram && (
                  <span className={styles.fieldError}>{fieldErrors.telegram}</span>
                )}
              </div>
            </>
          )}
          <div className={styles.field}>
            <label htmlFor="email" className={styles.label}>
              E-mail
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className={cn(styles.input, { [styles.inputError]: !!fieldErrors.email })}
              placeholder="example@mail.ru"
              autoComplete="email"
              aria-invalid={!!fieldErrors.email}
            />
            {fieldErrors.email && <span className={styles.fieldError}>{fieldErrors.email}</span>}
          </div>
          <div className={styles.field}>
            <label htmlFor="password" className={styles.label}>
              Пароль
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className={cn(styles.input, { [styles.inputError]: !!fieldErrors.password })}
              placeholder="••••••••"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              aria-invalid={!!fieldErrors.password}
            />
            {fieldErrors.password && (
              <span className={styles.fieldError}>{fieldErrors.password}</span>
            )}
          </div>
          {mode === 'login' && (
            <label className={styles.checkbox}>
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={e => setRememberMe(e.target.checked)}
              />
              <span>Запомнить меня</span>
            </label>
          )}
          {error && <div className={styles.error}>{error}</div>}
          <button type="submit" disabled={loading} className={styles.submit}>
            {loading ? 'Подождите...' : mode === 'login' ? 'Войти' : 'Зарегистрироваться'}
          </button>
        </form>

        <div className={styles.switch}>
          <button
            type="button"
            className={styles.switchBtn}
            onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
          >
            {mode === 'login'
              ? 'Нет аккаунта? Зарегистрироваться'
              : 'Уже есть аккаунт? Войти'}
          </button>
        </div>
      </div>
    </div>
  );
}
