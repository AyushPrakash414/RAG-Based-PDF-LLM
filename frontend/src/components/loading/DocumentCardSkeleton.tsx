import React from 'react';
import { NeoSkeleton, SkeletonRow, SkeletonCol } from './NeoSkeleton';

export const DocumentCardSkeleton: React.FC = () => (
  <div
    style={{
      backgroundColor: 'var(--card-bg)',
      border: 'var(--border-width) solid var(--border-color)',
      borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow)',
      padding: '1.5rem',
      display: 'flex',
      alignItems: 'center',
      gap: '1rem',
    }}
  >
    <NeoSkeleton variant="circle" width={40} height={40} />
    <SkeletonCol>
      <NeoSkeleton variant="title" width="70%" height={20} />
      <SkeletonRow>
        <NeoSkeleton variant="text" width={80} height={12} />
        <NeoSkeleton variant="text" width={60} height={12} />
      </SkeletonRow>
    </SkeletonCol>
    <SkeletonRow>
      <NeoSkeleton variant="circle" width={32} height={32} />
      <NeoSkeleton variant="circle" width={32} height={32} />
    </SkeletonRow>
  </div>
);
