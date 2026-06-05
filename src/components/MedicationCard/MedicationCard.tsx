import type { Medication } from '../../types';
import { getMedicationIcon } from '../../utils/medicationIcons';
import styles from './MedicationCard.module.scss';

interface MedicationCardProps {
  medication: Medication;
  onDelete?: () => void;
}

export const MedicationCard = ({ medication, onDelete }: MedicationCardProps) => {
  return (
    <div className={styles.card}>
      <div className={styles.image}>
        {medication.imageUrl ? (
          <img src={medication.imageUrl} alt={medication.name} />
        ) : (
          <div className={styles.icon}>{getMedicationIcon('таблетки')}</div>
        )}
      </div>
      <div className={styles.info}>
        <div className={styles.name}>{medication.name}</div>
        <div className={styles.description}>
          {medication.description != null && medication.description !== '' ? medication.description : '—'}
        </div>
      </div>
      {onDelete && (
        <button onClick={onDelete} className={styles.deleteButton}>
          ×
        </button>
      )}
    </div>
  );
};
