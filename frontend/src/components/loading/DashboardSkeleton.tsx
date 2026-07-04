import { NeoSkeleton } from './NeoSkeleton';
import { StatCardSkeleton } from './StatCardSkeleton';
import styles from '../../pages/Dashboard.module.css';

export const DashboardSkeleton: React.FC = () => {
  return (
    <div className={styles.dashboardContainer}>
      <header className={styles.header}>
        <NeoSkeleton variant="title" width="40%" height={40} style={{ marginBottom: '0.75rem' }} />
        <NeoSkeleton variant="text" width="60%" height={20} />
      </header>

      <div className={styles.statsGrid}>
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
      </div>
      
      <div className={styles.recentActivity}>
        <NeoSkeleton variant="title" width="20%" height={28} style={{ marginBottom: '1rem' }} />
        <div
          style={{
            backgroundColor: 'var(--card-bg)',
            border: 'var(--border-width) solid var(--border-color)',
            borderRadius: 'var(--radius)',
            boxShadow: 'var(--shadow)',
            padding: '2rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}
        >
          <NeoSkeleton variant="text" width="100%" height={16} />
          <NeoSkeleton variant="text" width="80%" height={16} />
          <NeoSkeleton variant="text" width="90%" height={16} />
        </div>
      </div>
    </div>
  );
};
