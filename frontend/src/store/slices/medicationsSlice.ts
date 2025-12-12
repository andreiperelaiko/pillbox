import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { Medication } from '../../types';
import { medicationsApi } from '../../api/medications';

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
  async (data: Omit<Medication, 'id' | 'createdAt'>) => {
    return medicationsApi.create(data);
  }
);

export const updateMedication = createAsyncThunk(
  'medications/update',
  async ({
    id,
    medication,
  }: {
    id: string;
    medication: Partial<Omit<Medication, 'id' | 'createdAt'>>;
  }) => {
    return medicationsApi.update(id, medication);
  }
);

export const deleteMedication = createAsyncThunk('medications/delete', async (id: string) => {
  await medicationsApi.delete(id);
  return id;
});

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
        state.items = action.payload;
      })
      .addCase(fetchMedications.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch medications';
      })
      // Create
      .addCase(createMedication.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createMedication.fulfilled, (state, action) => {
        state.loading = false;
        state.items.push(action.payload);
      })
      .addCase(createMedication.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to create medication';
      })
      // Update
      .addCase(updateMedication.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateMedication.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.items.findIndex(m => m.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
      })
      .addCase(updateMedication.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to update medication';
      })
      // Delete
      .addCase(deleteMedication.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteMedication.fulfilled, (state, action) => {
        state.loading = false;
        state.items = state.items.filter(m => m.id !== action.payload);
      })
      .addCase(deleteMedication.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to delete medication';
      });
  },
});

export default medicationsSlice.reducer;
