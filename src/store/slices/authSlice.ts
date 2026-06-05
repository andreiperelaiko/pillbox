import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import type { User } from '../../types';
import { toUserFriendlyError } from '../../utils/errorMessages';
import { ApiError } from '../../api/base';
import { authApi } from '../../api/auth';

const AUTH_STORAGE_KEY = 'tabletnica_auth';

function getStoredUser(): User | null {
  if (typeof localStorage === 'undefined') return null;
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as { user?: User };
    const u = data?.user;
    if (u && (typeof u.id === 'string' || typeof u.id === 'number') && typeof u.email === 'string')
      return u;
  } catch {
    // ignore
  }
  return null;
}

function persistUser(user: User | null): void {
  if (typeof localStorage === 'undefined') return;
  if (user) {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ user }));
  } else {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  }
}

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: getStoredUser(),
  loading: false,
  error: null,
};

export const registerUser = createAsyncThunk(
  'auth/register',
  async (
    data: {
      email: string;
      name: string;
      password: string;
      telegram?: string | null;
    },
    { rejectWithValue }
  ) => {
    try {
      // Регистрация создаёт аккаунт, но НЕ ставит сессионную cookie.
      // Поэтому сразу логинимся, чтобы получить сессию, и подтягиваем пользователя.
      await authApi.register(data);
      await authApi.login({ email: data.email, password: data.password });
      const user = await authApi.me();
      return user ?? null;
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        return rejectWithValue(toUserFriendlyError(error.message, error.status));
      }
      if (error instanceof Error) {
        return rejectWithValue(toUserFriendlyError(error.message));
      }
      return rejectWithValue('Не удалось зарегистрироваться. Попробуйте позже.');
    }
  }
);

export const loginUser = createAsyncThunk(
  'auth/login',
  async (
    data: {
      email: string;
      password: string;
      remember_me?: boolean;
    },
    { rejectWithValue }
  ) => {
    try {
      await authApi.login(data); // 200 → { message }, cookie pillbox_session ставится на сервере
      const user = await authApi.me(); // получаем текущего пользователя по сессии
      return user ?? null;
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        return rejectWithValue(toUserFriendlyError(error.message, error.status));
      }
      if (error instanceof Error) {
        return rejectWithValue(toUserFriendlyError(error.message));
      }
      return rejectWithValue('Не удалось войти. Попробуйте позже.');
    }
  }
);

export const fetchMe = createAsyncThunk('auth/me', async (_, { rejectWithValue }) => {
  try {
    return await authApi.me();
  } catch (error: unknown) {
    if (error instanceof ApiError) {
      return rejectWithValue(toUserFriendlyError(error.message, error.status));
    }
    if (error instanceof Error) {
      return rejectWithValue(toUserFriendlyError(error.message));
    }
    return rejectWithValue('Не удалось загрузить данные пользователя.');
  }
});

export const logoutUser = createAsyncThunk('auth/logout', async (_, { rejectWithValue }) => {
  try {
    await authApi.logout();
    return;
  } catch (error: unknown) {
    if (error instanceof ApiError) {
      return rejectWithValue(toUserFriendlyError(error.message, error.status));
    }
    if (error instanceof Error) {
      return rejectWithValue(toUserFriendlyError(error.message));
    }
    return rejectWithValue('Не удалось выйти из аккаунта.');
  }
});

export const logoutAllUser = createAsyncThunk('auth/logoutAll', async (_, { rejectWithValue }) => {
  try {
    await authApi.logoutAll();
    return;
  } catch (error: unknown) {
    if (error instanceof ApiError) {
      return rejectWithValue(toUserFriendlyError(error.message, error.status));
    }
    if (error instanceof Error) {
      return rejectWithValue(toUserFriendlyError(error.message));
    }
    return rejectWithValue('Не удалось выйти из всех аккаунтов.');
  }
});

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    /** Сброс пользователя без запроса к API (для 401, чтобы не вызывать POST /auth/logout и новый 401). */
    clearUser: state => {
      state.user = null;
      state.error = null;
      persistUser(null);
    },
  },
  extraReducers: builder => {
    builder
      // register
      .addCase(registerUser.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload ?? null;
        state.error = null;
        persistUser(state.user);
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.loading = false;
        state.error =
          (action.payload as string | undefined) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null) ||
          'Не удалось зарегистрироваться. Попробуйте позже.';
      })
      // login
      .addCase(loginUser.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload ?? null;
        state.error = null;
        persistUser(state.user);
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error =
          (action.payload as string | undefined) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null) ||
          'Не удалось войти. Попробуйте позже.';
      })
      // me
      .addCase(fetchMe.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMe.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload ?? null;
        state.error = null;
        persistUser(state.user ?? null);
      })
      .addCase(fetchMe.rejected, (state, action) => {
        state.loading = false;
        state.user = null;
        state.error =
          (action.payload as string | undefined) ||
          (action.error.message ? toUserFriendlyError(action.error.message) : null) ||
          'Не удалось загрузить данные пользователя.';
        persistUser(null);
      })
      // logout
      .addCase(logoutUser.fulfilled, state => {
        state.user = null;
        persistUser(null);
      })
      // logout all
      .addCase(logoutAllUser.fulfilled, state => {
        state.user = null;
        persistUser(null);
      });
  },
});

export const { clearUser } = authSlice.actions;
export default authSlice.reducer;
