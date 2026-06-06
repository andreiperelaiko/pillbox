import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { AppTheme, Settings } from '../../types';
import { getStoredTheme } from '../../components/ThemeApplier/ThemeApplier';

interface SettingsState extends Settings {
  loading: boolean;
  error: string | null;
}

const initialState: SettingsState = {
  notificationDelayMinutes: 1,
  theme: getStoredTheme(),
  loading: false,
  error: null,
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setNotificationDelayMinutes(state, action: { payload: number }) {
      state.notificationDelayMinutes = action.payload;
    },
    setTheme(state, action: PayloadAction<AppTheme>) {
      state.theme = action.payload;
    },
  },
});

export const { setNotificationDelayMinutes, setTheme } = settingsSlice.actions;
export default settingsSlice.reducer;
