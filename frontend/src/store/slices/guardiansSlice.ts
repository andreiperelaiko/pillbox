import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { GuardianResponse } from '../../api/guardians';
import { guardiansApi } from '../../api/guardians';
import type { GuardianAdd } from '../../api/guardians';
import { ApiError } from '../../api/base';
import { toUserFriendlyError } from '../../utils/errorMessages';

interface GuardiansState {
  items: GuardianResponse[];
  loading: boolean;
  error: string | null;
}

const initialState: GuardiansState = {
  items: [],
  loading: false,
  error: null,
};

/** Опекуны текущего пользователя. GET /guardians */
export const fetchGuardians = createAsyncThunk('guardians/fetchMy', async () => {
  return guardiansApi.getMyGuardians();
});

/** Текущий пользователь становится опекуном patientUserId. POST /guardians/attach/{user_id} */
export const attachAsGuardian = createAsyncThunk(
  'guardians/attach',
  async (
    { patientUserId, data }: { patientUserId: number; data: GuardianAdd },
    { rejectWithValue }
  ) => {
    try {
      return await guardiansApi.attachAsGuardian(patientUserId, data);
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        return rejectWithValue(toUserFriendlyError(error.message, error.status));
      }
      const msg =
        error instanceof Error ? error.message : 'Не удалось привязаться как опекун.';
      return rejectWithValue(toUserFriendlyError(msg));
    }
  }
);

const guardiansSlice = createSlice({
  name: 'guardians',
  initialState,
  reducers: {},
  extraReducers: builder => {
    builder
      .addCase(fetchGuardians.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchGuardians.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchGuardians.rejected, (state, action) => {
        state.loading = false;
        state.error =
          (action.payload as string) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null) ||
          'Не удалось загрузить опекунов.';
      })
      .addCase(attachAsGuardian.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(attachAsGuardian.fulfilled, state => {
        state.loading = false;
      })
      .addCase(attachAsGuardian.rejected, (state, action) => {
        state.loading = false;
        state.error =
          (action.payload as string) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null) ||
          'Не удалось привязаться как опекун.';
      });
  },
});

export default guardiansSlice.reducer;
