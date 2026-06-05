import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { Calendar } from '../../components/Calendar/Calendar';
import { IntakeCard } from '../../components/IntakeCard/IntakeCard';
import { markScheduleTaken } from '../../store/slices/schedulesSlice';
import { scheduleItemsToGroupedViews } from '../../utils/scheduleUtils';
import { checkMissedIntakes, getUpcomingIntakes } from '../../utils/notifications';
import styles from './HomePage.module.scss';

export const HomePage = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { items: scheduleItems } = useAppSelector(state => state.schedules);
  const { items: medications } = useAppSelector(state => state.medications);
  const settings = useAppSelector(state => state.settings);

  const groupedIntakes = useMemo(
    () => scheduleItemsToGroupedViews(scheduleItems || []),
    [scheduleItems]
  );

  const missedIntakes = useMemo(
    () =>
      checkMissedIntakes(
        groupedIntakes,
        settings || { notificationDelayMinutes: 30 }
      ).sort((a, b) => a.dateTime - b.dateTime),
    [groupedIntakes, settings]
  );
  const upcomingIntakes = useMemo(() => getUpcomingIntakes(groupedIntakes), [groupedIntakes]);

  const handleConfirm = async (scheduleId: number) => {
    try {
      await dispatch(markScheduleTaken({ schedule_id: scheduleId })).unwrap();
    } catch (error) {
      console.error('Failed to mark schedule as taken:', error);
    }
  };

  const handleDayClick = (date: Date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    navigate(`/intakes/day/${y}-${m}-${d}`);
  };

  const handleAddIntake = () => navigate('/intakes/add');

  const settingsWithDelay = settings || { notificationDelayMinutes: 30 };

  return (
    <div className={styles.homePage}>
      <div className={styles.mainLayout}>
        <div className={styles.calendarSection}>
          <Calendar
            intakes={groupedIntakes}
            settings={settingsWithDelay}
            onDayClick={handleDayClick}
            onAddIntake={handleAddIntake}
          />
        </div>

        <div className={styles.notifications}>
          {missedIntakes.length > 0 && (
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>Пропущенные приемы</h3>
              {missedIntakes.map(intake => (
                <IntakeCard
                  key={intake.id}
                  intake={intake}
                  medications={medications || []}
                  onConfirm={handleConfirm}
                />
              ))}
            </div>
          )}

          {upcomingIntakes.length > 0 && (
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>Ближайшие приемы</h3>
              {upcomingIntakes.map(intake => (
                <IntakeCard
                  key={intake.id}
                  intake={intake}
                  medications={medications || []}
                  onConfirm={handleConfirm}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
