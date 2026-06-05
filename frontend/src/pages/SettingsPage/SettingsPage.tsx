import { useAppDispatch } from '../../store/hooks';
import { logoutUser, logoutAllUser } from '../../store/slices/authSlice';
import { Button } from '../../components/Button/Button';
import styles from './SettingsPage.module.scss';

export const SettingsPage = () => {
  const dispatch = useAppDispatch();

  const handleLogout = () => {
    dispatch(logoutUser());
  };

  const handleLogoutAll = () => {
    dispatch(logoutAllUser());
  };

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Настройки</h1>

      <div className={styles.section}>
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
      </div>
    </div>
  );
};
