import { NeoSkeleton, SkeletonCol } from './NeoSkeleton';

export const StatCardSkeleton: React.FC = () => (
  <div
    style={{
      backgroundColor: 'var(--card-bg)',
      border: 'var(--border-width) solid var(--border-color)',
      borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow)',
      padding: '1.5rem',
      display: 'flex',
      alignItems: 'center',
      gap: '1.5rem',
    }}
  >
    <NeoSkeleton variant="circle" width={48} height={48} />
    <SkeletonCol>
      <NeoSkeleton variant="title" width="50%" height={32} />
      <NeoSkeleton variant="text" width="80%" />
    </SkeletonCol>
  </div>
);
