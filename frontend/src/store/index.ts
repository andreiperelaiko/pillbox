import { configureStore } from '@reduxjs/toolkit';
import medicationsReducer from './slices/medicationsSlice';
import schedulesReducer from './slices/schedulesSlice';
import guardiansReducer from './slices/guardiansSlice';
import wardsReducer from './slices/wardsSlice';
import settingsReducer from './slices/settingsSlice';
import authReducer from './slices/authSlice';

export const store = configureStore({
  reducer: {
    medications: medicationsReducer,
    schedules: schedulesReducer,
    guardians: guardiansReducer,
    wards: wardsReducer,
    settings: settingsReducer,
    auth: authReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
