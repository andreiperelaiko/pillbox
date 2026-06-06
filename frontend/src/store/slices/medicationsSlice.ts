import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { Medication, MedicationApiItem } from '../../types';
import { medicationsApi } from '../../api/medications';
import { ApiError } from '../../api/base';
import { toUserFriendlyError } from '../../utils/errorMessages';

function mapApiItemToMedication(item: MedicationApiItem): Medication {
  return {
    id: String(item.id),
    name: item.name,
    description: item.description ?? undefined,
    form: 'таблетки',
    defaultAmount: 0,
    imageUrl: null,
    createdAt: Date.now(),
  };
}

interface MedicationsState {
  items: Medication[];
  loading: boolean;
  error: string | null;
}

const initialState: MedicationsState = {
  items: [],
  loading: false,
  error: null,
};

export const fetchMedications = createAsyncThunk('medications/fetchAll', async () => {
  return medicationsApi.getAll();
});

export const createMedication = createAsyncThunk(
  'medications/create',
  async (data: { name: string; description?: string | null }) => {
    return medicationsApi.create(data);
  }
);

export const deleteMedication = createAsyncThunk(
  'medications/delete',
  async (medicationId: string, { rejectWithValue }) => {
    try {
      await medicationsApi.delete(Number(medicationId));
      return Number(medicationId);
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        return rejectWithValue(toUserFriendlyError(error.message, error.status));
      }
      const msg = error instanceof Error ? error.message : 'Не удалось удалить лекарство.';
      return rejectWithValue(toUserFriendlyError(msg));
    }
  }
);

const medicationsSlice = createSlice({
  name: 'medications',
  initialState,
  reducers: {},
  extraReducers: builder => {
    builder
      // Fetch all
      .addCase(fetchMedications.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMedications.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.map(mapApiItemToMedication);
      })
      .addCase(fetchMedications.rejected, (state, action) => {
        state.loading = false;
        state.error =
          (action.payload as string) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null) ||
          'Не удалось загрузить список лекарств.';
      })
      // Create
      .addCase(createMedication.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createMedication.fulfilled, (state, action) => {
        state.loading = false;
        state.items.push(mapApiItemToMedication(action.payload));
      })
      .addCase(createMedication.rejected, (state, action) => {
        state.loading = false;
        state.error =
          (action.payload as string) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null) ||
          'Не удалось добавить лекарство.';
      })
      .addCase(deleteMedication.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteMedication.fulfilled, (state, action) => {
        state.loading = false;
        state.items = state.items.filter(item => Number(item.id) !== action.payload);
      })
      .addCase(deleteMedication.rejected, (state, action) => {
        state.loading = false;
        state.error =
          (action.payload as string) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null) ||
          'Не удалось удалить лекарство.';
      });
  },
});

export default medicationsSlice.reducer;
