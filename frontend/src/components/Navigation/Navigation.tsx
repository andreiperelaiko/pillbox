import { Link, useLocation } from 'react-router-dom';
import styles from './Navigation.module.scss';
import cn from 'classnames';

export const Navigation = () => {
  const location = useLocation();

  const links = [
    { path: '/', label: 'Главная' },
    { path: '/medications', label: 'Медикаменты' },
    { path: '/caregivers', label: 'Опекуны' },
    { path: '/settings', label: 'Настройки' },
  ];

  return (
    <nav className={styles.nav}>
      <div className={styles.logo}>
        <Link to="/" className={styles.logoLink}>
          <div className={styles.logoTitle}>Таблетница</div>
          <div className={styles.logoTagline}>Забота о самых близких</div>
        </Link>
      </div>
      <div className={styles.links}>
        {links.map(link => (
          <Link
            key={link.path}
            to={link.path}
            className={cn(styles.link, {
              [styles.active]: location.pathname === link.path,
            })}
          >
            {link.label}
          </Link>
        ))}
      </div>
    </nav>
  );
};
