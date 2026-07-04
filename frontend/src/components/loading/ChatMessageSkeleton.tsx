import React from 'react';
import { NeoSkeleton, SkeletonCol } from './NeoSkeleton';

interface ChatMessageSkeletonProps {
  role?: 'user' | 'assistant';
}

export const ChatMessageSkeleton: React.FC<ChatMessageSkeletonProps> = ({ role = 'assistant' }) => {
  const isUser = role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        gap: '0.75rem',
        alignItems: 'flex-start',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        padding: '0.5rem 0',
      }}
    >
      {!isUser && <NeoSkeleton variant="avatar" />}
      <div
        style={{
          backgroundColor: 'var(--card-bg)',
          border: 'var(--border-width) solid var(--border-color)',
          borderRadius: 'var(--radius)',
          boxShadow: 'var(--shadow)',
          padding: '1rem',
          maxWidth: '65%',
          minWidth: '200px',
        }}
      >
        <SkeletonCol>
          <NeoSkeleton variant="text" width="100%" />
          <NeoSkeleton variant="text" width="90%" />
          <NeoSkeleton variant="text" width={isUser ? '60%' : '75%'} />
          <NeoSkeleton variant="text" width={60} height={10} style={{ marginTop: '0.5rem' }} />
        </SkeletonCol>
      </div>
      {isUser && <NeoSkeleton variant="avatar" />}
    </div>
  );
};
