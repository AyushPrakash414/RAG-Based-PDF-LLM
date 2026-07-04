import { NeoSkeleton } from './NeoSkeleton';

export const ChatSidebarSkeleton: React.FC = () => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
    {/* New Chat button skeleton */}
    <NeoSkeleton variant="button" width="100%" height={44} />

    {/* Session items */}
    {Array.from({ length: 5 }, (_, i) => (
      <div
        key={i}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          padding: '0.75rem',
          backgroundColor: 'var(--card-bg)',
          border: '2px solid var(--skeleton-border)',
          borderRadius: 'var(--radius)',
        }}
      >
        <NeoSkeleton variant="circle" width={20} height={20} />
        <NeoSkeleton variant="text" width="80%" height={14} />
      </div>
    ))}
  </div>
);
