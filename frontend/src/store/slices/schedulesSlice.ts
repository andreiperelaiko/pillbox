import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { ScheduleItem } from '../../types';
import { schedulesApi } from '../../api/schedules';
import type { CreateSchedulePayload } from '../../api/schedules';
import { ApiError } from '../../api/base';
import { toUserFriendlyError } from '../../utils/errorMessages';

interface SchedulesState {
  items: ScheduleItem[];
  loading: boolean;
  error: string | null;
}

const initialState: SchedulesState = {
  items: [],
  loading: false,
  error: null,
};

export const fetchSchedules = createAsyncThunk('schedules/fetchAll', async () => {
  return schedulesApi.getAll();
});

export const createSchedule = createAsyncThunk(
  'schedules/create',
  async (data: CreateSchedulePayload) => {
    return schedulesApi.create(data);
  }
);

export const markScheduleTaken = createAsyncThunk(
  'schedules/markTaken',
  async (payload: { schedule_id: number }, { getState, rejectWithValue }) => {
    try {
      // medication_id нужен для пути запроса — берём из уже загруженного приёма.
      const state = getState() as { schedules: SchedulesState };
      const item = state.schedules.items.find(i => i.id === payload.schedule_id);
      if (!item) {
        return rejectWithValue('Приём не найден. Обновите страницу.');
      }
      return await schedulesApi.markTaken({
        medication_id: item.medication_id,
        schedule_id: payload.schedule_id,
      });
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        return rejectWithValue(toUserFriendlyError(error.message, error.status));
      }
      const msg = error instanceof Error ? error.message : 'Не удалось отметить приём.';
      return rejectWithValue(toUserFriendlyError(msg));
    }
  }
);

// У API нет эндпоинта удаления приёма — сообщаем об этом понятно.
export const deleteSchedule = createAsyncThunk(
  'schedules/delete',
  async (_scheduleId: number, { rejectWithValue }) => {
    return rejectWithValue('Удаление приёма не поддерживается сервером.');
  }
);

const schedulesSlice = createSlice({
  name: 'schedules',
  initialState,
  reducers: {},
  extraReducers: builder => {
    builder
      .addCase(fetchSchedules.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSchedules.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchSchedules.rejected, (state, action) => {
        state.loading = false;
        state.error =
          (action.payload as string) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null) ||
          'Не удалось загрузить приёмы.';
      })
      .addCase(createSchedule.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createSchedule.fulfilled, (state, action) => {
        state.loading = false;
        state.items.push(action.payload);
      })
      .addCase(createSchedule.rejected, (state, action) => {
        state.loading = false;
        state.error =
          (action.payload as string) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null) ||
          'Не удалось создать приём.';
      })
      .addCase(markScheduleTaken.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(markScheduleTaken.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.items.findIndex(i => i.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
      })
      .addCase(markScheduleTaken.rejected, (state, action) => {
        state.loading = false;
        state.error =
          (action.payload as string) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null) ||
          'Не удалось отметить приём.';
      })
      .addCase(deleteSchedule.rejected, (state, action) => {
        state.error =
          (action.payload as string) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null) ||
          'Не удалось удалить приём.';
      });
  },
});

export default schedulesSlice.reducer;
