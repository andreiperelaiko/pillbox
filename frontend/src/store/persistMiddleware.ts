import { Middleware } from '@reduxjs/toolkit';

export const persistMiddleware: Middleware = store => next => action => {
  const result = next(action);
  const state = store.getState();
  localStorage.setItem('tabletnica-storage', JSON.stringify(state));
  return result;
};

export const loadState = () => {
  try {
    const serializedState = localStorage.getItem('tabletnica-storage');
    if (serializedState === null) {
      return undefined;
    }
    return JSON.parse(serializedState);
  } catch (err) {
    return undefined;
  }
};
