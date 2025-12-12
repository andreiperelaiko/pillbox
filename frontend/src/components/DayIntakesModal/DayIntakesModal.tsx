import { format } from 'date-fns';
import ru from 'date-fns/locale/ru';
import type { MedicationIntake, Medication } from '../../types';
import { IntakeCard } from '../IntakeCard/IntakeCard';
import styles from './DayIntakesModal.module.scss';

interface DayIntakesModalProps {
  isOpen: boolean;
  onClose: () => void;
  date: Date;
  intakes: MedicationIntake[];
  medications: Medication[];
  onConfirm: (intakeId: string, medicationId: string) => void;
  onEdit: (intake: MedicationIntake) => void;
  onDelete: (intake: MedicationIntake) => void;
  onAddIntake: () => void;
}

export const DayIntakesModal = ({
  isOpen,
  onClose,
  date,
  intakes,
  medications,
  onConfirm,
  onEdit,
  onDelete,
  onAddIntake,
}: DayIntakesModalProps) => {
  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <h2 className={styles.title}>Приемы на {format(date, 'd MMMM yyyy', { locale: ru })}</h2>
          <button onClick={onClose} className={styles.closeButton}>
            ×
          </button>
        </div>

        <div className={styles.addButtonContainer}>
          <button onClick={onAddIntake} className={styles.addButton}>
            + Добавить прием
          </button>
        </div>

        <div className={styles.content}>
          {intakes.length === 0 ? (
            <div className={styles.empty}>Нет приемов на этот день</div>
          ) : (
            <div className={styles.intakesList}>
              {intakes
                .sort((a, b) => a.dateTime - b.dateTime)
                .map(intake => (
                  <div key={intake.id} className={styles.intakeWrapper}>
                    <IntakeCard
                      intake={intake}
                      medications={medications}
                      onConfirm={medicationId => onConfirm(intake.id, medicationId)}
                    />
                    <div className={styles.actions}>
                      <button onClick={() => onEdit(intake)} className={styles.editButton}>
                        Редактировать
                      </button>
                      <button onClick={() => onDelete(intake)} className={styles.deleteButton}>
                        Удалить
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
