import { useState } from 'react';
import { useAppSelector } from '../../store/hooks';
import { Calendar } from '../../components/Calendar/Calendar';
import { IntakeCard } from '../../components/IntakeCard/IntakeCard';
import { AddIntakeModal } from '../../components/AddIntakeModal/AddIntakeModal';
import { DayIntakesModal } from '../../components/DayIntakesModal/DayIntakesModal';
import { EditIntakeModal } from '../../components/EditIntakeModal/EditIntakeModal';
import { confirmMedicationInIntake } from '../../store/slices/intakesSlice';
import { useAppDispatch } from '../../store/hooks';
import { checkMissedIntakes, getUpcomingIntakes } from '../../utils/notifications';
import type { MedicationIntake } from '../../types';
import styles from './HomePage.module.scss';

export const HomePage = () => {
  const dispatch = useAppDispatch();
  const { items: intakes } = useAppSelector(state => state.intakes);
  const { items: medications } = useAppSelector(state => state.medications);
  const settings = useAppSelector(state => state.settings);

  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [isAddIntakeModalOpen, setIsAddIntakeModalOpen] = useState(false);
  const [isDayIntakesModalOpen, setIsDayIntakesModalOpen] = useState(false);
  const [isEditIntakeModalOpen, setIsEditIntakeModalOpen] = useState(false);
  const [editingIntake, setEditingIntake] = useState<MedicationIntake | null>(null);
  const [editModalMode, setEditModalMode] = useState<'edit' | 'delete'>('edit');
  const [modalInitialDate, setModalInitialDate] = useState<Date | undefined>(undefined);

  const missedIntakes = checkMissedIntakes(
    intakes || [],
    settings || { notificationDelayMinutes: 30 }
  ).sort((a, b) => a.dateTime - b.dateTime);
  const upcomingIntakes = getUpcomingIntakes(intakes || []);

  const selectedDateIntakes = selectedDate
    ? (intakes || []).filter(intake => {
        const intakeDate = new Date(intake.dateTime);
        const isSameDate =
          intakeDate.getDate() === selectedDate.getDate() &&
          intakeDate.getMonth() === selectedDate.getMonth() &&
          intakeDate.getFullYear() === selectedDate.getFullYear();
        return isSameDate;
      })
    : [];

  const handleConfirm = async (intakeId: string, medicationId: string) => {
    try {
      await dispatch(confirmMedicationInIntake({ intakeId, medicationId })).unwrap();
    } catch (error) {
      console.error('Failed to confirm medication:', error);
    }
  };

  const handleDayClick = (date: Date) => {
    setSelectedDate(date);
    setIsDayIntakesModalOpen(true);
  };

  const handleAddIntakeClick = () => {
    setModalInitialDate(undefined);
    setIsAddIntakeModalOpen(true);
  };

  const handleEditIntake = (intake: MedicationIntake) => {
    setEditingIntake(intake);
    setEditModalMode('edit');
    setIsEditIntakeModalOpen(true);
    setIsDayIntakesModalOpen(false);
  };

  const handleDeleteIntake = (intake: MedicationIntake) => {
    setEditingIntake(intake);
    setEditModalMode('delete');
    setIsEditIntakeModalOpen(true);
    setIsDayIntakesModalOpen(false);
  };

  const handleAddIntakeFromDayModal = () => {
    if (selectedDate) {
      setModalInitialDate(selectedDate);
      setIsAddIntakeModalOpen(true);
      setIsDayIntakesModalOpen(false);
    }
  };

  return (
    <div className={styles.homePage}>
      <div className={styles.mainLayout}>
        <div className={styles.calendarSection}>
          <Calendar
            intakes={intakes || []}
            settings={settings || { notificationDelayMinutes: 30 }}
            onDayClick={handleDayClick}
            onAddIntake={handleAddIntakeClick}
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
                  medications={medications}
                  onConfirm={medicationId => handleConfirm(intake.id, medicationId)}
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
                  medications={medications}
                  onConfirm={medicationId => handleConfirm(intake.id, medicationId)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      <AddIntakeModal
        isOpen={isAddIntakeModalOpen}
        onClose={() => {
          setIsAddIntakeModalOpen(false);
          setModalInitialDate(undefined);
        }}
        initialDate={modalInitialDate}
      />

      {selectedDate && (
        <DayIntakesModal
          isOpen={isDayIntakesModalOpen}
          onClose={() => {
            setIsDayIntakesModalOpen(false);
            setSelectedDate(null);
          }}
          date={selectedDate}
          intakes={selectedDateIntakes}
          medications={medications}
          onConfirm={(intakeId, medicationId) => handleConfirm(intakeId, medicationId)}
          onEdit={handleEditIntake}
          onDelete={handleDeleteIntake}
          onAddIntake={handleAddIntakeFromDayModal}
        />
      )}

      <EditIntakeModal
        isOpen={isEditIntakeModalOpen}
        onClose={() => {
          setIsEditIntakeModalOpen(false);
          setEditingIntake(null);
          setEditModalMode('edit');
        }}
        intake={editingIntake}
        initialMode={editModalMode}
      />
    </div>
  );
};
