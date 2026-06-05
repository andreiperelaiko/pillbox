import { createSlice } from '@reduxjs/toolkit';
import type { Settings } from '../../types';

interface SettingsState extends Settings {
  loading: boolean;
  error: string | null;
}

const initialState: SettingsState = {
  notificationDelayMinutes: 30,
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
  },
});

export const { setNotificationDelayMinutes } = settingsSlice.actions;
export default settingsSlice.reducer;
