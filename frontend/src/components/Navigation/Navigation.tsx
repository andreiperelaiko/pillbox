import { Link, useLocation } from 'react-router-dom';
import styles from './Navigation.module.scss';
import cn from 'classnames';

const icons = {
  calendar: (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  ),
  pill: (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.5 20.5L3.5 13.5a3 3 0 0 1 0-4.24l6.36-6.36a3 3 0 0 1 4.24 0l7 7a3 3 0 0 1 0 4.24l-6.36 6.36a3 3 0 0 1-4.24 0z" />
      <line x1="14" y1="10" x2="10" y2="14" />
    </svg>
  ),
  caregivers: (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  settings: (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  ),
};

const links: Array<{ path: string; label: string; icon: keyof typeof icons }> = [
  { path: '/', label: 'Главная', icon: 'calendar' },
  { path: '/medications', label: 'Медикаменты', icon: 'pill' },
  { path: '/caregivers', label: 'Опекуны/Подопечные', icon: 'caregivers' },
  { path: '/settings', label: 'Настройки', icon: 'settings' },
];

export const Navigation = () => {
  const location = useLocation();

  return (
    <>
      <header className={styles.header}>
        <div className={styles.logo}>
          <Link to="/" className={styles.logoLink}>
            <span className={styles.logoTitle}>Таблетница</span>
            <span className={styles.logoTagline}>Забота о самых близких</span>
          </Link>
        </div>
        <div className={styles.linksDesktop}>
          {links.map(link => (
            <Link
              key={link.path}
              to={link.path}
              className={cn(styles.linkDesktop, {
                [styles.active]: location.pathname === link.path,
              })}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </header>

      <nav className={styles.bottomNav} aria-label="Меню">
        {links.map(link => (
          <Link
            key={link.path}
            to={link.path}
            className={cn(styles.linkIcon, {
              [styles.active]: location.pathname === link.path,
            })}
            title={link.label}
          >
            <span className={styles.icon}>{icons[link.icon]}</span>
            <span className={styles.linkLabel}>{link.label}</span>
          </Link>
        ))}
      </nav>
    </>
  );
};
