import { useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import ru from 'date-fns/locale/ru';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { markScheduleTaken, deleteSchedule } from '../../store/slices/schedulesSlice';
import { scheduleItemsToGroupedViews } from '../../utils/scheduleUtils';
import { formatDateLocal } from '../../utils/dateUtils';
import { IntakeCard } from '../../components/IntakeCard/IntakeCard';
import { Button } from '../../components/Button/Button';
import { ConfirmModal } from '../../components/ConfirmModal/ConfirmModal';
import styles from './DayIntakesPage.module.scss';

export const DayIntakesPage = () => {
  const { dateStr } = useParams<{ dateStr: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { items: scheduleItems } = useAppSelector(state => state.schedules);
  const { items: medications } = useAppSelector(state => state.medications);
  const [scheduleToDelete, setScheduleToDelete] = useState<number | null>(null);

  const date = useMemo(() => {
    if (!dateStr || !/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return null;
    const [y, m, d] = dateStr.split('-').map(Number);
    const dt = new Date(y, m - 1, d);
    return isNaN(dt.getTime()) ? null : dt;
  }, [dateStr]);

  const groupedIntakes = useMemo(
    () => scheduleItemsToGroupedViews(scheduleItems || []),
    [scheduleItems]
  );

  const dayIntakes = useMemo(() => {
    if (!date) return [];
    return groupedIntakes.filter(intake => {
      const d = new Date(intake.dateTime);
      return (
        d.getDate() === date.getDate() &&
        d.getMonth() === date.getMonth() &&
        d.getFullYear() === date.getFullYear()
      );
    });
  }, [date, groupedIntakes]);

  const handleConfirm = async (scheduleId: number) => {
    try {
      await dispatch(markScheduleTaken({ schedule_id: scheduleId })).unwrap();
    } catch (error) {
      console.error('Failed to mark schedule as taken:', error);
    }
  };

  const handleConfirmDelete = () => {
    if (scheduleToDelete !== null) {
      dispatch(deleteSchedule(scheduleToDelete));
      setScheduleToDelete(null);
    }
  };

  const handleAddIntake = () => {
    if (date) {
      navigate(`/intakes/add?date=${formatDateLocal(date)}`);
    } else {
      navigate('/intakes/add');
    }
  };

  if (!dateStr || !date) {
    return (
      <div className={styles.page}>
        <p className={styles.error}>Неверная дата в адресе.</p>
        <Button onClick={() => navigate('/')}>На главную</Button>
      </div>
    );
  }

  const sortedIntakes = [...dayIntakes].sort((a, b) => a.dateTime - b.dateTime);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          Приёмы на {format(date, 'd MMMM yyyy', { locale: ru })}
        </h1>
        <Button type="button" variant="secondary" onClick={() => navigate(-1)} className={styles.back}>
          Назад
        </Button>
      </div>

      <div className={styles.addButtonContainer}>
        <Button onClick={handleAddIntake} className={styles.addButton}>
          + Добавить прием
        </Button>
      </div>

      <div className={styles.content}>
        {sortedIntakes.length === 0 ? (
          <div className={styles.empty}>Нет приемов на этот день</div>
        ) : (
          <div className={styles.intakesList}>
            {sortedIntakes.map(intake => (
              <div key={intake.id} className={styles.intakeWrapper}>
                <IntakeCard
                  intake={intake}
                  medications={medications || []}
                  onConfirm={handleConfirm}
                  onDelete={setScheduleToDelete}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      <ConfirmModal
        open={scheduleToDelete !== null}
        title="Удалить приём?"
        message="Приём будет удалён из расписания. Это действие нельзя отменить."
        confirmLabel="Удалить"
        cancelLabel="Отмена"
        variant="danger"
        onConfirm={handleConfirmDelete}
        onCancel={() => setScheduleToDelete(null)}
      />
    </div>
  );
};
