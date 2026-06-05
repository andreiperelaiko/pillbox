import { useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { fetchMedications } from '../../store/slices/medicationsSlice';
import { fetchSchedules } from '../../store/slices/schedulesSlice';
import { fetchGuardians } from '../../store/slices/guardiansSlice';
import { fetchWards } from '../../store/slices/wardsSlice';
import { Navigation } from '../Navigation/Navigation';
import { HomePage } from '../../pages/HomePage/HomePage';
import { MedicationsPage } from '../../pages/MedicationsPage/MedicationsPage';
import { CaregiversPage } from '../../pages/CaregiversPage/CaregiversPage';
import { GuardiansAttachPage } from '../../pages/GuardiansAttachPage/GuardiansAttachPage';
import { AddIntakePage } from '../../pages/AddIntakePage/AddIntakePage';
import { DayIntakesPage } from '../../pages/DayIntakesPage/DayIntakesPage';
import { SettingsPage } from '../../pages/SettingsPage/SettingsPage';
import { AuthPage } from '../../pages/Auth/AuthPage';
import styles from '../../App.module.scss';

export const AppRoutes = () => {
  const dispatch = useAppDispatch();
  const user = useAppSelector(state => state.auth.user);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (user && location.pathname === '/auth') {
      navigate('/', { replace: true });
    }
  }, [user, location.pathname, navigate]);

  useEffect(() => {
    if (!user || location.pathname === '/auth') return;
    dispatch(fetchMedications());
    dispatch(fetchSchedules());
    dispatch(fetchGuardians());
    dispatch(fetchWards());
  }, [dispatch, user, location.pathname]);

  if (!user) {
    return (
      <Routes>
        <Route path="/auth" element={<AuthPage />} />
        <Route path="*" element={<Navigate to="/auth" replace />} />
      </Routes>
    );
  }

  return (
    <>
      <Navigation />
      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/intakes/add" element={<AddIntakePage />} />
          <Route path="/intakes/day/:dateStr" element={<DayIntakesPage />} />
          <Route path="/medications" element={<MedicationsPage />} />
          <Route path="/caregivers" element={<CaregiversPage />} />
          <Route path="/guardians/attach" element={<GuardiansAttachPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </>
  );
};
