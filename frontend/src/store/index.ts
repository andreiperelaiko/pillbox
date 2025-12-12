import { configureStore } from '@reduxjs/toolkit';
import medicationsReducer from './slices/medicationsSlice';
import intakesReducer from './slices/intakesSlice';
import caregiversReducer from './slices/caregiversSlice';
import settingsReducer from './slices/settingsSlice';

export const store = configureStore({
  reducer: {
    medications: medicationsReducer,
    intakes: intakesReducer,
    caregivers: caregiversReducer,
    settings: settingsReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
