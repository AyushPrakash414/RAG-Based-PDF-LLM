import { NeoSkeleton, SkeletonRow } from './NeoSkeleton';

export const SourcesPanelSkeleton: React.FC = () => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
    <NeoSkeleton variant="title" width="60%" height={22} />
    <NeoSkeleton variant="text" width="90%" height={14} />

    <div
      style={{
        backgroundColor: 'var(--card-bg)',
        border: 'var(--border-width) solid var(--border-color)',
        borderRadius: 'var(--radius)',
        boxShadow: 'var(--shadow)',
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
      }}
    >
      <SkeletonRow>
        <NeoSkeleton variant="circle" width={24} height={24} />
        <NeoSkeleton variant="text" width="70%" height={16} />
      </SkeletonRow>
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <NeoSkeleton variant="text" width={100} height={28} style={{ borderRadius: '8px' }} />
        <NeoSkeleton variant="text" width={120} height={28} style={{ borderRadius: '8px' }} />
        <NeoSkeleton variant="text" width={90} height={28} style={{ borderRadius: '8px' }} />
      </div>
      <NeoSkeleton variant="text" width="50%" height={14} />
    </div>
  </div>
);
