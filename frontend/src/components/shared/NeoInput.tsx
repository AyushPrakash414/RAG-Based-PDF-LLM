import React from 'react';
import styles from './NeoInput.module.css';

interface NeoInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const NeoInput = React.forwardRef<HTMLInputElement, NeoInputProps>(
  ({ label, error, icon, className = '', ...props }, ref) => {
    return (
      <div className={`${styles.inputWrapper} ${className}`}>
        {label && <label className={styles.label}>{label}</label>}
        <div className={styles.inputContainer}>
          {icon && <span className={styles.icon}>{icon}</span>}
          <input 
            ref={ref}
            className={`${styles.neoInput} ${icon ? styles.withIcon : ''} ${error ? styles.hasError : ''}`} 
            {...props} 
          />
        </div>
        {error && <span className={styles.errorMessage}>{error}</span>}
      </div>
    );
  }
);

NeoInput.displayName = 'NeoInput';
