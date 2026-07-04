import React from 'react';
import styles from './NeoSkeleton.module.css';

type SkeletonVariant = 'text' | 'title' | 'avatar' | 'button' | 'input' | 'card' | 'circle';

interface NeoSkeletonProps {
  variant?: SkeletonVariant;
  width?: string | number;
  height?: string | number;
  className?: string;
  count?: number;
  style?: React.CSSProperties;
}

export const NeoSkeleton: React.FC<NeoSkeletonProps> = ({
  variant = 'text',
  width,
  height,
  className = '',
  count = 1,
  style,
}) => {
  const elements = Array.from({ length: count }, (_, i) => (
    <div
      key={i}
      className={`${styles.skeleton} ${styles[variant]} ${count > 1 ? styles.stagger : ''} ${className}`}
      style={{
        ...(width ? { width: typeof width === 'number' ? `${width}px` : width } : {}),
        ...(height ? { height: typeof height === 'number' ? `${height}px` : height } : {}),
        ...style,
      }}
      aria-hidden="true"
    />
  ));

  return <>{elements}</>;
};

/* Helper layout components */
export const SkeletonRow: React.FC<{ children: React.ReactNode; className?: string; style?: React.CSSProperties }> = ({ children, className = '', style }) => (
  <div className={`${styles.row} ${className}`} style={style}>{children}</div>
);

export const SkeletonCol: React.FC<{ children: React.ReactNode; className?: string; style?: React.CSSProperties }> = ({ children, className = '', style }) => (
  <div className={`${styles.col} ${className}`} style={style}>{children}</div>
);
