import type { GroupedIntakeView, Medication } from '../../types';
import { formatDateTimeLocal } from '../../utils/dateUtils';
import styles from './IntakeCard.module.scss';
import cn from 'classnames';

interface IntakeCardProps {
  intake: GroupedIntakeView;
  medications: Medication[];
  onConfirm: (scheduleId: number) => void;
  onDelete?: (scheduleId: number) => void;
}

export const IntakeCard = ({ intake, medications, onConfirm, onDelete }: IntakeCardProps) => {
  const dateTime = new Date(intake.dateTime);
  const timeLabel = formatDateTimeLocal(dateTime, 'HH:mm');
  const dateLabel = formatDateTimeLocal(dateTime, 'd MMMM');
  const isPast = dateTime < new Date();
  const allConfirmed = intake.medications.every(m => m.confirmed);

  return (
    <div className={cn(styles.card, { [styles.past]: isPast, [styles.confirmed]: allConfirmed })}>
      <div className={styles.header}>
        <div className={styles.time}>{timeLabel}</div>
        <div className={styles.date}>{dateLabel}</div>
      </div>

      <div className={styles.medications}>
        {intake.medications.map(m => {
          const medication = medications.find(med => med.id === m.medicationId);
          if (!medication) return null;

          return (
            <div
              key={m.scheduleId}
              className={cn(styles.medication, { [styles.confirmed]: m.confirmed })}
            >
              <div className={styles.medicationInfo}>
                <div className={styles.medicationName}>{medication.name}</div>
                <div className={styles.dose}>{m.doseDisplay}</div>
              </div>
              <div className={styles.actions}>
                {!m.confirmed && (
                  <button
                    onClick={() => onConfirm(m.scheduleId)}
                    className={styles.confirmButton}
                    title="Отметить приём"
                  >
                    ✓
                  </button>
                )}
                {m.confirmed && <div className={styles.confirmedBadge}>✓</div>}
                {onDelete && (
                  <button
                    type="button"
                    onClick={() => onDelete(m.scheduleId)}
                    className={styles.deleteButton}
                    title="Удалить приём"
                  >
                    ×
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
