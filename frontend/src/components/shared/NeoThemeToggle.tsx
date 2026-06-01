import React, { useEffect, useState } from 'react';
import { Sun, Moon } from 'lucide-react';
import styles from './NeoThemeToggle.module.css';

export const NeoThemeToggle: React.FC = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    const currentTheme = savedTheme || 'light';
    setTheme(currentTheme);
    document.documentElement.setAttribute('data-theme', currentTheme);
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  return (
    <button 
      className={`${styles.toggleBtn} ${theme === 'dark' ? styles.dark : ''}`}
      onClick={toggleTheme}
      title="Toggle Theme"
    >
      <div className={styles.iconContainer}>
        {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
      </div>
    </button>
  );
};
