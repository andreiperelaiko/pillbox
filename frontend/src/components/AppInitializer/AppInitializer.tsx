import { useEffect } from 'react';
import { useAppDispatch } from '../../store/hooks';
import { fetchMedications } from '../../store/slices/medicationsSlice';
import { fetchIntakes } from '../../store/slices/intakesSlice';
import { fetchCaregivers } from '../../store/slices/caregiversSlice';
import { fetchSettings } from '../../store/slices/settingsSlice';

export const AppInitializer = ({ children }: { children: React.ReactNode }) => {
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(fetchMedications());
    dispatch(fetchIntakes());
    dispatch(fetchCaregivers());
    dispatch(fetchSettings());
  }, [dispatch]);

  return <>{children}</>;
};
