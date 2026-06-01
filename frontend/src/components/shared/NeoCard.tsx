import React from 'react';
import styles from './NeoCard.module.css';

interface NeoCardProps extends React.HTMLAttributes<HTMLDivElement> {
  noPadding?: boolean;
}

export const NeoCard: React.FC<NeoCardProps> = ({ 
  children, 
  className = '', 
  noPadding = false,
  ...props 
}) => {
  return (
    <div 
      className={`${styles.neoCard} ${noPadding ? styles.noPadding : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
