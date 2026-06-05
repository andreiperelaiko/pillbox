import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { removeWard } from '../../store/slices/wardsSlice';
import { Button } from '../../components/Button/Button';
import { ConfirmModal } from '../../components/ConfirmModal/ConfirmModal';
import styles from './CaregiversPage.module.scss';

export const CaregiversPage = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { items: guardians } = useAppSelector(state => state.guardians);
  const { items: wards } = useAppSelector(state => state.wards);
  const [wardToRemove, setWardToRemove] = useState<number | null>(null);

  const handleConfirmRemoveWard = () => {
    if (wardToRemove !== null) {
      dispatch(removeWard(wardToRemove));
      setWardToRemove(null);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Опекуны/Подопечные</h1>
        <Button type="button" onClick={() => navigate('/guardians/attach')}>
          Стать опекуном
        </Button>
      </div>

      <div className={styles.sectionsGrid}>
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Мои подопечные</h2>
          <div className={styles.list}>
            {(wards || []).length === 0 ? (
              <div className={styles.empty}>Нет подопечных</div>
            ) : (
              (wards || []).map(w => (
                <div key={w.id} className={styles.card}>
                  <div className={styles.info}>
                    <div className={styles.name}>{w.name}</div>
                    <div className={styles.contact}>{w.email}</div>
                    {w.relationship != null && w.relationship !== '' && (
                      <div className={styles.contact}>{w.relationship}</div>
                    )}
                  </div>
                  <Button
                    type="button"
                    variant="danger"
                    onClick={() => setWardToRemove(w.id)}
                    className={styles.removeButton}
                  >
                    Удалить
                  </Button>
                </div>
              ))
            )}
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Мои опекуны</h2>
          <div className={styles.list}>
            {(guardians || []).length === 0 ? (
              <div className={styles.empty}>Нет опекунов</div>
            ) : (
              (guardians || []).map(g => (
                <div key={g.id} className={styles.card}>
                  <div className={styles.info}>
                    <div className={styles.name}>{g.name}</div>
                    <div className={styles.contact}>{g.email}</div>
                    {g.relationship != null && g.relationship !== '' && (
                      <div className={styles.contact}>{g.relationship}</div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <ConfirmModal
        open={wardToRemove !== null}
        title="Отказаться от опекунства?"
        message="Вы перестанете получать уведомления о пропущенных приёмах этого подопечного."
        confirmLabel="Удалить"
        cancelLabel="Отмена"
        variant="danger"
        onConfirm={handleConfirmRemoveWard}
        onCancel={() => setWardToRemove(null)}
      />
    </div>
  );
};
