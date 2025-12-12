import { useState, useEffect } from 'react';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { updateIntake, deleteIntake, fetchIntakes } from '../../store/slices/intakesSlice';
import { Button } from '../Button/Button';
import { Input } from '../Input/Input';
import { Select } from '../Select/Select';
import { getMedicationIcon } from '../../utils/medicationIcons';
import { getUnitByForm } from '../../utils/medicationUnits';
import { getRelatedIntakes } from '../../utils/intakeUtils';
import type { MedicationIntake, MedicationDose, MedicationForm } from '../../types';
import styles from './EditIntakeModal.module.scss';

interface EditIntakeModalProps {
  isOpen: boolean;
  onClose: () => void;
  intake: MedicationIntake | null;
  initialMode?: 'edit' | 'delete';
}

type EditScope = 'all' | 'this' | 'previous' | 'next';
type DeleteScope = 'all' | 'this' | 'previous' | 'next';

export const EditIntakeModal = ({
  isOpen,
  onClose,
  intake,
  initialMode = 'edit',
}: EditIntakeModalProps) => {
  const dispatch = useAppDispatch();
  const { items: allIntakes } = useAppSelector(state => state.intakes);
  const { items: medications } = useAppSelector(state => state.medications);

  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [selectedMedications, setSelectedMedications] = useState<
    Array<{
      medicationId: string;
      amount: string;
    }>
  >([]);
  const [editScope, setEditScope] = useState<EditScope>('this');
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteScope, setDeleteScope] = useState<DeleteScope>('this');
  const [medicationNameFilter, setMedicationNameFilter] = useState('');
  const [medicationTypeFilter, setMedicationTypeFilter] = useState<MedicationForm | 'all'>('all');

  const relatedIntakes = intake ? getRelatedIntakes(intake, allIntakes) : null;
  const isRepeating =
    relatedIntakes && (relatedIntakes.previous.length > 0 || relatedIntakes.next.length > 0);

  useEffect(() => {
    if (intake) {
      const intakeDate = new Date(intake.dateTime);
      setDate(intakeDate.toISOString().split('T')[0]);
      setTime(
        `${intakeDate.getHours().toString().padStart(2, '0')}:${intakeDate
          .getMinutes()
          .toString()
          .padStart(2, '0')}`
      );
      setSelectedMedications(
        intake.medications.map(m => ({
          medicationId: m.medicationId,
          amount: m.amount.toString(),
        }))
      );
      setEditScope('this');
      setIsDeleting(initialMode === 'delete');
    }
  }, [intake, initialMode]);

  const updateMedicationAmount = (medicationId: string, amount: string) => {
    setSelectedMedications(
      selectedMedications.map(m => (m.medicationId === medicationId ? { ...m, amount } : m))
    );
  };

  const medicationForms: MedicationForm[] = [
    'таблетки',
    'капсулы',
    'жидкость',
    'укол',
    'порошок',
    'мазь',
    'спрей',
  ];

  const filteredMedications = (medications || []).filter(medication => {
    const matchesName = medication.name.toLowerCase().includes(medicationNameFilter.toLowerCase());
    const matchesType = medicationTypeFilter === 'all' || medication.form === medicationTypeFilter;
    return matchesName && matchesType;
  });

  const toggleMedication = (medicationId: string) => {
    const existing = selectedMedications.find(m => m.medicationId === medicationId);
    if (existing) {
      setSelectedMedications(selectedMedications.filter(m => m.medicationId !== medicationId));
    } else {
      const medication = (medications || []).find(m => m.id === medicationId);
      if (medication) {
        setSelectedMedications([
          ...selectedMedications,
          {
            medicationId,
            amount: medication.defaultAmount.toString(),
          },
        ]);
      }
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!intake || selectedMedications.length === 0) return;

    const dateTime = new Date(`${date}T${time}`).getTime();
    const medicationDoses: MedicationDose[] = selectedMedications.map(m => {
      const medication = (medications || []).find(med => med.id === m.medicationId);
      // Сохраняем confirmed статус из текущего приема, если медикамент уже был там
      const existingMed = intake.medications.find(med => med.medicationId === m.medicationId);
      return {
        medicationId: m.medicationId,
        amount: Number(m.amount),
        unit: medication ? getUnitByForm(medication.form) : 'таблетки',
        confirmed: existingMed?.confirmed || false,
      };
    });

    try {
      if (!relatedIntakes) {
        const result = await dispatch(
          updateIntake({
            id: intake.id,
            intake: {
              dateTime,
              medications: medicationDoses,
              seriesId: intake.seriesId, // Сохраняем seriesId
            },
          })
        );
        if (updateIntake.rejected.match(result)) {
          throw new Error(
            (result.payload as string) || result.error?.message || 'Failed to update intake'
          );
        }
        // Перезагружаем список с сервера для синхронизации
        await dispatch(fetchIntakes());
      } else {
        const intakesToUpdate: MedicationIntake[] = [];

        if (editScope === 'all') {
          intakesToUpdate.push(
            ...relatedIntakes.previous,
            relatedIntakes.current,
            ...relatedIntakes.next
          );
        } else if (editScope === 'this') {
          intakesToUpdate.push(relatedIntakes.current);
        } else if (editScope === 'previous') {
          intakesToUpdate.push(...relatedIntakes.previous, relatedIntakes.current);
        } else if (editScope === 'next') {
          intakesToUpdate.push(relatedIntakes.current, ...relatedIntakes.next);
        }

        // Обновляем приемы последовательно, чтобы избежать проблем с параллельными обновлениями
        const results = [];
        const errors = [];

        for (const intakeToUpdate of intakesToUpdate) {
          try {
            // Для каждого приема сохраняем confirmed статус его текущих медикаментов
            const updatedMedications = medicationDoses.map(newMed => {
              const existingMed = intakeToUpdate.medications.find(
                m => m.medicationId === newMed.medicationId
              );
              return {
                ...newMed,
                confirmed: existingMed?.confirmed || newMed.confirmed || false,
              };
            });

            const result = await dispatch(
              updateIntake({
                id: intakeToUpdate.id,
                intake: {
                  dateTime:
                    intakeToUpdate.dateTime === intake.dateTime
                      ? dateTime
                      : intakeToUpdate.dateTime,
                  medications: updatedMedications,
                  seriesId: intakeToUpdate.seriesId, // Сохраняем seriesId
                },
              })
            );

            if (updateIntake.rejected.match(result)) {
              const errorMsg =
                (result.payload as string) ||
                result.error?.message ||
                `Failed to update intake ${intakeToUpdate.id}`;
              errors.push(errorMsg);
              console.warn(`Failed to update intake ${intakeToUpdate.id}:`, errorMsg);
            } else {
              results.push(result);
            }
          } catch (error: unknown) {
            const errorMsg =
              error instanceof Error
                ? error.message
                : `Failed to update intake ${intakeToUpdate.id}`;
            errors.push(errorMsg);
            console.warn(`Error updating intake ${intakeToUpdate.id}:`, error);
          }
        }

        // Если были ошибки, но хотя бы один прием обновлен - показываем предупреждение
        if (errors.length > 0) {
          if (results.length === 0) {
            // Все обновления провалились
            throw new Error(`Не удалось обновить приемы: ${errors.join(', ')}`);
          } else {
            // Частичный успех - показываем предупреждение, но продолжаем
            console.warn('Some intakes could not be updated:', errors);
            alert(
              `Предупреждение: ${errors.length} из ${intakesToUpdate.length} приемов не удалось обновить`
            );
          }
        }

        // Перезагружаем список с сервера для синхронизации
        await dispatch(fetchIntakes());
      }

      onClose();
    } catch (error: unknown) {
      console.error('Failed to update intake:', error);
      const errorMessage = error instanceof Error ? error.message : 'Ошибка при обновлении приема';
      alert(errorMessage);
    }
  };

  const handleDelete = async () => {
    if (!intake) return;

    try {
      if (!relatedIntakes) {
        // Одиночный прием
        const result = await dispatch(deleteIntake(intake.id));
        // Проверяем, что операция успешна (не rejected)
        if (deleteIntake.fulfilled.match(result)) {
          // Перезагружаем список с сервера для синхронизации
          await dispatch(fetchIntakes());
          onClose();
        } else if (deleteIntake.rejected.match(result)) {
          const errorMessage =
            (result.payload as string) || result.error?.message || 'Failed to delete intake';
          throw new Error(errorMessage);
        }
        return;
      }

      const intakesToDelete: MedicationIntake[] = [];

      if (deleteScope === 'this') {
        intakesToDelete.push(relatedIntakes.current);
      } else if (deleteScope === 'all') {
        intakesToDelete.push(
          ...relatedIntakes.previous,
          relatedIntakes.current,
          ...relatedIntakes.next
        );
      } else if (deleteScope === 'previous') {
        intakesToDelete.push(...relatedIntakes.previous, relatedIntakes.current);
      } else if (deleteScope === 'next') {
        intakesToDelete.push(relatedIntakes.current, ...relatedIntakes.next);
      }

      // Удаляем приемы последовательно, чтобы избежать проблем
      const results = [];
      const errors = [];

      for (const intakeToDelete of intakesToDelete) {
        try {
          const result = await dispatch(deleteIntake(intakeToDelete.id));
          if (deleteIntake.rejected.match(result)) {
            const errorMsg =
              (result.payload as string) ||
              result.error?.message ||
              `Failed to delete intake ${intakeToDelete.id}`;
            errors.push(errorMsg);
            console.warn(`Failed to delete intake ${intakeToDelete.id}:`, errorMsg);
          } else {
            results.push(result);
          }
        } catch (error: unknown) {
          const errorMsg =
            error instanceof Error ? error.message : `Failed to delete intake ${intakeToDelete.id}`;
          errors.push(errorMsg);
          console.warn(`Error deleting intake ${intakeToDelete.id}:`, error);
        }
      }

      // Если были ошибки, но хотя бы один прием удален - показываем предупреждение
      if (errors.length > 0) {
        if (results.length === 0) {
          // Все удаления провалились
          throw new Error(`Не удалось удалить приемы: ${errors.join(', ')}`);
        } else {
          // Частичный успех - показываем предупреждение, но продолжаем
          console.warn('Some intakes could not be deleted:', errors);
          alert(
            `Предупреждение: ${errors.length} из ${intakesToDelete.length} приемов не удалось удалить`
          );
        }
      }

      // Если все успешно - перезагружаем список с сервера
      await dispatch(fetchIntakes());
      onClose();
    } catch (error: unknown) {
      console.error('Failed to delete intake:', error);
      const errorMessage = error instanceof Error ? error.message : 'Ошибка при удалении приема';
      alert(errorMessage);
    }
  };

  if (!isOpen || !intake) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <h2 className={styles.title}>{isDeleting ? 'Удалить прием' : 'Редактировать прием'}</h2>
          <button onClick={onClose} className={styles.closeButton}>
            ×
          </button>
        </div>

        {isDeleting ? (
          <div className={styles.content}>
            {isRepeating ? (
              <>
                <p className={styles.message}>
                  Этот прием является частью повторяющейся серии. Что вы хотите удалить?
                </p>
                <div className={styles.scopeOptions}>
                  <label className={styles.radioLabel}>
                    <input
                      type="radio"
                      value="this"
                      checked={deleteScope === 'this'}
                      onChange={e => setDeleteScope(e.target.value as DeleteScope)}
                    />
                    Только этот прием
                  </label>
                  <label className={styles.radioLabel}>
                    <input
                      type="radio"
                      value="all"
                      checked={deleteScope === 'all'}
                      onChange={e => setDeleteScope(e.target.value as DeleteScope)}
                    />
                    Все приемы в серии
                  </label>
                  <label className={styles.radioLabel}>
                    <input
                      type="radio"
                      value="previous"
                      checked={deleteScope === 'previous'}
                      onChange={e => setDeleteScope(e.target.value as DeleteScope)}
                    />
                    Этот и предыдущие приемы
                  </label>
                  <label className={styles.radioLabel}>
                    <input
                      type="radio"
                      value="next"
                      checked={deleteScope === 'next'}
                      onChange={e => setDeleteScope(e.target.value as DeleteScope)}
                    />
                    Этот и последующие приемы
                  </label>
                </div>
              </>
            ) : (
              <p className={styles.message}>Вы уверены, что хотите удалить этот прием?</p>
            )}
            <div className={styles.actions}>
              <Button variant="secondary" onClick={() => setIsDeleting(false)}>
                Отмена
              </Button>
              <Button variant="danger" onClick={handleDelete}>
                Удалить
              </Button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSave} className={styles.form}>
            <div className={styles.dateTimeRow}>
              <Input
                label="Дата"
                type="date"
                value={date}
                onChange={e => setDate(e.target.value)}
                required
              />
              <Input
                label="Время"
                type="time"
                value={time}
                onChange={e => setTime(e.target.value)}
                required
              />
            </div>

            {isRepeating && (
              <div className={styles.scopeSection}>
                <label className={styles.label}>Область применения изменений:</label>
                <div className={styles.scopeOptions}>
                  <label className={styles.radioLabel}>
                    <input
                      type="radio"
                      value="this"
                      checked={editScope === 'this'}
                      onChange={e => setEditScope(e.target.value as EditScope)}
                    />
                    Только этот прием
                  </label>
                  <label className={styles.radioLabel}>
                    <input
                      type="radio"
                      value="all"
                      checked={editScope === 'all'}
                      onChange={e => setEditScope(e.target.value as EditScope)}
                    />
                    Все приемы в серии
                  </label>
                  <label className={styles.radioLabel}>
                    <input
                      type="radio"
                      value="previous"
                      checked={editScope === 'previous'}
                      onChange={e => setEditScope(e.target.value as EditScope)}
                    />
                    Этот и предыдущие приемы
                  </label>
                  <label className={styles.radioLabel}>
                    <input
                      type="radio"
                      value="next"
                      checked={editScope === 'next'}
                      onChange={e => setEditScope(e.target.value as EditScope)}
                    />
                    Этот и последующие приемы
                  </label>
                </div>
              </div>
            )}

            <div className={styles.medications}>
              <label className={styles.label}>Лекарства:</label>
              <div className={styles.medicationFilters}>
                <Input
                  label="Поиск по названию"
                  placeholder="Введите название..."
                  value={medicationNameFilter}
                  onChange={e => setMedicationNameFilter(e.target.value)}
                  onClear={() => setMedicationNameFilter('')}
                />
                <Select
                  label="Фильтр по типу"
                  value={medicationTypeFilter}
                  onChange={value => setMedicationTypeFilter(value as MedicationForm | 'all')}
                  options={[
                    { value: 'all', label: 'Все типы' },
                    ...medicationForms.map(form => ({ value: form, label: form })),
                  ]}
                />
              </div>
              <div className={styles.medicationsList}>
                {filteredMedications.length === 0 ? (
                  <div className={styles.empty}>
                    {medications.length === 0 ? 'Нет доступных лекарств' : 'Ничего не найдено'}
                  </div>
                ) : (
                  filteredMedications.map(medication => {
                    const selected = selectedMedications.find(
                      m => m.medicationId === medication.id
                    );
                    return (
                      <div key={medication.id} className={styles.medicationItem}>
                        <label className={styles.medicationCheckbox}>
                          <input
                            type="checkbox"
                            checked={!!selected}
                            onChange={() => toggleMedication(medication.id)}
                          />
                          <div className={styles.medicationImage}>
                            {medication.imageUrl ? (
                              <img src={medication.imageUrl} alt={medication.name} />
                            ) : (
                              <div className={styles.medicationIcon}>
                                {getMedicationIcon(medication.form)}
                              </div>
                            )}
                          </div>
                          <div className={styles.medicationInfo}>
                            <div className={styles.medicationName}>{medication.name}</div>
                            <div className={styles.medicationForm}>{medication.form}</div>
                          </div>
                        </label>
                        {selected && (
                          <div className={styles.doseInputs}>
                            <div className={styles.doseInputWrapper}>
                              <Input
                                type="number"
                                value={selected.amount}
                                onChange={e =>
                                  updateMedicationAmount(medication.id, e.target.value)
                                }
                                min="1"
                              />
                            </div>
                            <div className={styles.doseUnit}>{getUnitByForm(medication.form)}</div>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            <div className={styles.actions}>
              <Button type="button" variant="secondary" onClick={() => setIsDeleting(true)}>
                Удалить
              </Button>
              <Button type="button" variant="secondary" onClick={onClose}>
                Отмена
              </Button>
              <Button type="submit">Сохранить</Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
