import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { WardResponse } from '../../api/wards';
import { wardsApi } from '../../api/wards';
import { ApiError } from '../../api/base';
import { toUserFriendlyError } from '../../utils/errorMessages';

interface WardsState {
  items: WardResponse[];
  loading: boolean;
  error: string | null;
}

const initialState: WardsState = {
  items: [],
  loading: false,
  error: null,
};

/** Подопечные текущего пользователя. GET /api/wards */
export const fetchWards = createAsyncThunk('wards/fetchMy', async () => {
  return wardsApi.getMyWards();
});

/** Отказаться от опекунства. DELETE /api/wards/{user_id} */
export const removeWard = createAsyncThunk(
  'wards/remove',
  async (userId: number, { rejectWithValue }) => {
    try {
      await wardsApi.removeWard(userId);
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        return rejectWithValue(toUserFriendlyError(error.message, error.status));
      }
      const msg =
        error instanceof Error ? error.message : 'Не удалось отказаться от опекунства.';
      return rejectWithValue(toUserFriendlyError(msg));
    }
  }
);

const wardsSlice = createSlice({
  name: 'wards',
  initialState,
  reducers: {},
  extraReducers: builder => {
    builder
      .addCase(fetchWards.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchWards.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchWards.rejected, (state, action) => {
        state.loading = false;
        state.error =
          (action.payload as string) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null) ||
          'Не удалось загрузить подопечных.';
      })
      .addCase(removeWard.fulfilled, (state, action) => {
        state.items = state.items.filter(w => w.id !== action.meta.arg);
      })
      .addCase(removeWard.rejected, (state, action) => {
        state.error =
          (action.payload as string) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null);
      });
  },
});

export default wardsSlice.reducer;
