import { format } from 'date-fns';
import ru from 'date-fns/locale/ru';
import type { MedicationIntake, Medication } from '../../types';
import styles from './IntakeCard.module.scss';
import cn from 'classnames';

interface IntakeCardProps {
  intake: MedicationIntake;
  medications: Medication[];
  onConfirm: (medicationId: string) => void;
}

export const IntakeCard = ({ intake, medications, onConfirm }: IntakeCardProps) => {
  const dateTime = new Date(intake.dateTime);
  const isPast = dateTime < new Date();
  const allConfirmed = intake.medications.every(m => m.confirmed);
  console.log(intake);
  return (
    <div className={cn(styles.card, { [styles.past]: isPast, [styles.confirmed]: allConfirmed })}>
      <div className={styles.header}>
        <div className={styles.time}>{format(dateTime, 'HH:mm', { locale: ru })}</div>
        <div className={styles.date}>{format(dateTime, 'd MMMM', { locale: ru })}</div>
      </div>

      <div className={styles.medications}>
        {intake.medications.map(medicationDose => {
          const medication = medications.find(m => m.id === medicationDose.medicationId);
          if (!medication) return null;

          return (
            <div
              key={medicationDose.medicationId}
              className={cn(styles.medication, {
                [styles.confirmed]: medicationDose.confirmed,
              })}
            >
              <div className={styles.medicationInfo}>
                <div className={styles.medicationName}>{medication.name}</div>
                <div className={styles.dose}>
                  {medicationDose.amount} {medicationDose.unit}
                </div>
              </div>
              {!medicationDose.confirmed && (
                <button
                  onClick={() => onConfirm(medicationDose.medicationId)}
                  className={styles.confirmButton}
                >
                  ✓
                </button>
              )}
              {medicationDose.confirmed && <div className={styles.confirmedBadge}>✓</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
};
