import { useState } from 'react';
import {
  format,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameDay,
  addMonths,
  subMonths,
} from 'date-fns';
import ru from 'date-fns/locale/ru';
import type { MedicationIntake, Settings } from '../../types';
import { getIntakeStatus } from '../../utils/intakeStatus';
import styles from './Calendar.module.scss';
import cn from 'classnames';

interface CalendarProps {
  intakes: MedicationIntake[];
  settings: Settings;
  onDayClick?: (date: Date) => void;
  onAddIntake?: () => void;
}

export const Calendar = ({ intakes, settings, onDayClick, onAddIntake }: CalendarProps) => {
  const [currentDate, setCurrentDate] = useState(new Date());

  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd });

  const getIntakesForDay = (date: Date) => {
    return (intakes || []).filter(intake => isSameDay(new Date(intake.dateTime), date));
  };

  const handlePrevMonth = () => {
    setCurrentDate(subMonths(currentDate, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(addMonths(currentDate, 1));
  };

  return (
    <div className={styles.calendar}>
      <div className={styles.header}>
        <button onClick={handlePrevMonth} className={styles.navButton}>
          ←
        </button>
        <h2 className={styles.monthTitle}>{format(currentDate, 'LLLL yyyy', { locale: ru })}</h2>
        <button onClick={handleNextMonth} className={styles.navButton}>
          →
        </button>
      </div>
      {onAddIntake && (
        <div className={styles.addButtonContainer}>
          <button onClick={onAddIntake} className={styles.addButton}>
            + Добавить прием
          </button>
        </div>
      )}

      <div className={styles.weekdays}>
        {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map(day => (
          <div key={day} className={styles.weekday}>
            {day}
          </div>
        ))}
      </div>

      <div className={styles.days}>
        {days.map(day => {
          const dayIntakes = getIntakesForDay(day);
          const isToday = isSameDay(day, new Date());

          return (
            <div
              key={day.toISOString()}
              className={cn(styles.day, { [styles.today]: isToday })}
              onClick={() => onDayClick?.(day)}
            >
              <div className={styles.dayNumber}>{format(day, 'd')}</div>
              {dayIntakes.length > 0 && (
                <div className={styles.intakes}>
                  {dayIntakes.slice(0, 3).map(intake => {
                    const status = getIntakeStatus(intake, settings);
                    return (
                      <div
                        key={intake.id}
                        className={cn(styles.intakeDot, {
                          [styles.completed]: status === 'completed',
                          [styles.completedPast]: status === 'completedPast',
                          [styles.pending]: status === 'pending',
                          [styles.missed]: status === 'missed',
                        })}
                      />
                    );
                  })}
                  {dayIntakes.length > 3 && (
                    <div className={styles.moreIntakes}>+{dayIntakes.length - 3}</div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
