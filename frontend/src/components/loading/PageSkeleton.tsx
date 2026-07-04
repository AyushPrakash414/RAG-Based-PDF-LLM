import { NeoSkeleton, SkeletonRow } from './NeoSkeleton';
import styles from '../../pages/Landing.module.css';

export const PageSkeleton: React.FC = () => {
  return (
    <div className={styles.landingContainer}>
      <nav className={styles.navbar}>
        <SkeletonRow>
          <NeoSkeleton variant="circle" width={28} height={28} />
          <NeoSkeleton variant="title" width={150} height={24} style={{ margin: 0 }} />
        </SkeletonRow>
        <SkeletonRow>
          <NeoSkeleton variant="text" width={50} height={16} />
          <NeoSkeleton variant="button" width={110} height={40} />
        </SkeletonRow>
      </nav>

      <main className={styles.main}>
        <section className={styles.hero} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
          <NeoSkeleton variant="title" width="70%" height={48} style={{ alignSelf: 'center' }} />
          <NeoSkeleton variant="text" width="50%" height={20} style={{ alignSelf: 'center' }} />
          <SkeletonRow style={{ justifyContent: 'center', marginTop: '1rem' }}>
            <NeoSkeleton variant="button" width={140} height={44} />
            <NeoSkeleton variant="button" width={140} height={44} />
          </SkeletonRow>
        </section>

        <section className={styles.features}>
          {Array.from({ length: 3 }, (_, i) => (
            <div
              key={i}
              style={{
                backgroundColor: 'var(--card-bg)',
                border: 'var(--border-width) solid var(--border-color)',
                borderRadius: 'var(--radius)',
                boxShadow: 'var(--shadow)',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <NeoSkeleton variant="circle" width={32} height={32} />
              <NeoSkeleton variant="title" width="60%" height={24} />
              <NeoSkeleton variant="text" width="100%" height={16} />
              <NeoSkeleton variant="text" width="80%" height={16} />
            </div>
          ))}
        </section>

        <section className={styles.architecture}>
          <NeoSkeleton variant="title" width="30%" height={32} style={{ alignSelf: 'center', marginBottom: '1.5rem' }} />
          <div className={styles.flowContainer}>
            <NeoSkeleton variant="card" style={{ flex: 1, height: 60 }} />
            <NeoSkeleton variant="circle" width={24} height={24} />
            <NeoSkeleton variant="card" style={{ flex: 1, height: 60 }} />
            <NeoSkeleton variant="circle" width={24} height={24} />
            <NeoSkeleton variant="card" style={{ flex: 1, height: 60 }} />
          </div>
        </section>
      </main>

      <footer className={styles.footer}>
        <NeoSkeleton variant="text" width="40%" height={16} style={{ margin: '0 auto' }} />
      </footer>
    </div>
  );
};
