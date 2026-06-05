import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { fetchMedications } from '../../store/slices/medicationsSlice';
import { fetchSchedules } from '../../store/slices/schedulesSlice';
import { fetchGuardians } from '../../store/slices/guardiansSlice';
import { fetchWards } from '../../store/slices/wardsSlice';
import { fetchMe, clearUser } from '../../store/slices/authSlice';
import { setUnauthorizedHandler } from '../../api/unauthorizedHandler';
import { checkHealth } from '../../api/health';

export const AppInitializer = ({ children }: { children: React.ReactNode }) => {
  const dispatch = useAppDispatch();
  const user = useAppSelector(state => state.auth.user);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      dispatch(clearUser());
      if (window.location.pathname !== '/auth') {
        window.location.href = '/auth';
      }
    });
    return () => setUnauthorizedHandler(null);
  }, [dispatch]);

  useEffect(() => {
    if (window.location.pathname === '/auth') return;
    let cancelled = false;
    (async () => {
      await checkHealth();
      if (cancelled) return;
      dispatch(fetchMe());
    })();
    return () => {
      cancelled = true;
    };
  }, [dispatch]);

  useEffect(() => {
    if (!user) return;
    dispatch(fetchMedications());
    dispatch(fetchSchedules());
    dispatch(fetchGuardians());
    dispatch(fetchWards());
  }, [dispatch, user]);

  return <>{children}</>;
};
