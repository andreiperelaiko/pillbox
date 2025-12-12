import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { Settings } from '../../types';
import { settingsApi } from '../../api/settings';

interface SettingsState extends Settings {
  loading: boolean;
  error: string | null;
}

const initialState: SettingsState = {
  notificationDelayMinutes: 30,
  loading: false,
  error: null,
};

export const fetchSettings = createAsyncThunk('settings/fetch', async () => {
  return settingsApi.get();
});

export const updateSettings = createAsyncThunk(
  'settings/update',
  async (data: Partial<Settings>) => {
    return settingsApi.update(data);
  }
);

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {},
  extraReducers: builder => {
    builder
      // Fetch
      .addCase(fetchSettings.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSettings.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
        if (action.payload) {
          state.notificationDelayMinutes = action.payload.notificationDelayMinutes ?? 30;
        }
      })
      .addCase(fetchSettings.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch settings';
      })
      // Update
      .addCase(updateSettings.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateSettings.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
        if (action.payload) {
          state.notificationDelayMinutes =
            action.payload.notificationDelayMinutes ?? state.notificationDelayMinutes;
        }
      })
      .addCase(updateSettings.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to update settings';
      });
  },
});

export default settingsSlice.reducer;
