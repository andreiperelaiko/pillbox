import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { MedicationIntake } from '../../types';
import { intakesApi } from '../../api/intakes';

interface IntakesState {
  items: MedicationIntake[];
  loading: boolean;
  error: string | null;
}

const initialState: IntakesState = {
  items: [],
  loading: false,
  error: null,
};

export const fetchIntakes = createAsyncThunk('intakes/fetchAll', async () => {
  return intakesApi.getAll();
});

export const createIntake = createAsyncThunk(
  'intakes/create',
  async (data: Omit<MedicationIntake, 'id' | 'createdAt'>) => {
    return intakesApi.create(data);
  }
);

export const updateIntake = createAsyncThunk(
  'intakes/update',
  async ({
    id,
    intake,
  }: {
    id: string;
    intake: Partial<Omit<MedicationIntake, 'id' | 'createdAt'>>;
  }) => {
    return intakesApi.update(id, intake);
  }
);

export const deleteIntake = createAsyncThunk(
  'intakes/delete',
  async (id: string, { rejectWithValue }) => {
    try {
      await intakesApi.delete(id);
      return id;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete intake';
      return rejectWithValue(errorMessage);
    }
  }
);

export const confirmMedicationInIntake = createAsyncThunk(
  'intakes/confirmMedication',
  async ({ intakeId, medicationId }: { intakeId: string; medicationId: string }) => {
    return intakesApi.confirmMedication(intakeId, medicationId);
  }
);

const intakesSlice = createSlice({
  name: 'intakes',
  initialState,
  reducers: {},
  extraReducers: builder => {
    builder
      // Fetch all
      .addCase(fetchIntakes.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchIntakes.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchIntakes.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch intakes';
      })
      // Create
      .addCase(createIntake.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createIntake.fulfilled, (state, action) => {
        state.loading = false;
        state.items.push(action.payload);
      })
      .addCase(createIntake.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to create intake';
      })
      // Update
      .addCase(updateIntake.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateIntake.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.items.findIndex(i => i.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
      })
      .addCase(updateIntake.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to update intake';
      })
      // Delete
      .addCase(deleteIntake.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteIntake.fulfilled, (state, action) => {
        state.loading = false;
        state.items = state.items.filter(i => i.id !== action.payload);
      })
      .addCase(deleteIntake.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to delete intake';
      })
      // Confirm medication
      .addCase(confirmMedicationInIntake.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(confirmMedicationInIntake.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.items.findIndex(i => i.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
      })
      .addCase(confirmMedicationInIntake.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to confirm medication';
      });
  },
});

export default intakesSlice.reducer;
