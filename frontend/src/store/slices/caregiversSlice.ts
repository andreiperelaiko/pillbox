import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { Caregiver } from '../../types';
import { caregiversApi } from '../../api/caregivers';

interface CaregiversState {
  items: Caregiver[];
  loading: boolean;
  error: string | null;
}

const initialState: CaregiversState = {
  items: [],
  loading: false,
  error: null,
};

export const fetchCaregivers = createAsyncThunk('caregivers/fetchAll', async () => {
  return caregiversApi.getAll();
});

export const createCaregiver = createAsyncThunk(
  'caregivers/create',
  async (data: Omit<Caregiver, 'id' | 'createdAt'>) => {
    return caregiversApi.create(data);
  }
);

export const updateCaregiver = createAsyncThunk(
  'caregivers/update',
  async ({
    id,
    caregiver,
  }: {
    id: string;
    caregiver: Partial<Omit<Caregiver, 'id' | 'createdAt'>>;
  }) => {
    return caregiversApi.update(id, caregiver);
  }
);

export const deleteCaregiver = createAsyncThunk('caregivers/delete', async (id: string) => {
  await caregiversApi.delete(id);
  return id;
});

const caregiversSlice = createSlice({
  name: 'caregivers',
  initialState,
  reducers: {},
  extraReducers: builder => {
    builder
      // Fetch all
      .addCase(fetchCaregivers.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCaregivers.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchCaregivers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch caregivers';
      })
      // Create
      .addCase(createCaregiver.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createCaregiver.fulfilled, (state, action) => {
        state.loading = false;
        state.items.push(action.payload);
      })
      .addCase(createCaregiver.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to create caregiver';
      })
      // Update
      .addCase(updateCaregiver.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateCaregiver.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.items.findIndex(c => c.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
      })
      .addCase(updateCaregiver.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to update caregiver';
      })
      // Delete
      .addCase(deleteCaregiver.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteCaregiver.fulfilled, (state, action) => {
        state.loading = false;
        state.items = state.items.filter(c => c.id !== action.payload);
      })
      .addCase(deleteCaregiver.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to delete caregiver';
      });
  },
});

export default caregiversSlice.reducer;
