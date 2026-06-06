import { api } from './base';
import { medicationsApi } from './medications';
import type { ScheduleItem } from '../types';

/**
 * Тело создания приёма. medication_id определяет лекарство (уходит в путь),
 * intake_at и dose — в тело запроса.
 */
export interface CreateSchedulePayload {
  medication_id: number;
  intake_at: string; // ISO 8601, e.g. "2026-03-07T08:00:00Z"
  dose?: string | null;
}

/** Отметить приём выполненным. Нужен medication_id (путь) и schedule_id (тело). */
export interface MarkTakenPayload {
  medication_id: number;
  schedule_id: number;
}

export interface DeleteSchedulePayload {
  medication_id: number;
  schedule_id: number;
}

/**
 * Расписания вложены в лекарство (общего эндпоинта /schedules у API нет):
 * GET  /medications/{medication_id}/schedules            — приёмы по лекарству
 * POST /medications/{medication_id}/schedules            — создать приём (201)
 * POST   /medications/{medication_id}/schedules/mark-taken — отметить выполненным (200)
 * DELETE /medications/{medication_id}/schedules/{schedule_id} — удалить приём (204)
 */
export const schedulesApi = {
  /** Все приёмы пользователя = объединение расписаний по всем его лекарствам. */
  getAll: async (): Promise<ScheduleItem[]> => {
    const meds = await medicationsApi.getAll();
    const lists = await Promise.all(
      meds.map(m =>
        api
          .get<ScheduleItem[]>(`/medications/${m.id}/schedules`)
          .catch(() => [] as ScheduleItem[])
      )
    );
    return lists.flat();
  },

  create: ({ medication_id, intake_at, dose }: CreateSchedulePayload) =>
    api.post<ScheduleItem>(`/medications/${medication_id}/schedules`, { intake_at, dose }),

  markTaken: ({ medication_id, schedule_id }: MarkTakenPayload) =>
    api.post<ScheduleItem>(`/medications/${medication_id}/schedules/mark-taken`, {
      schedule_id,
    }),

  delete: ({ medication_id, schedule_id }: DeleteSchedulePayload) =>
    api.delete<void>(`/medications/${medication_id}/schedules/${schedule_id}`),
};
