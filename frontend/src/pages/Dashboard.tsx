import React from 'react';
import { FileText, MessageSquare, Bot, BarChart } from 'lucide-react';
import { NeoCard } from '../components/shared/NeoCard';
import { useAuth } from '../context/AuthContext';
import styles from './Dashboard.module.css';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className={styles.dashboardContainer}>
      <header className={styles.header}>
        <h1>Welcome, {user?.name?.split(' ')[0]}!</h1>
        <p>Here is an overview of your activity.</p>
      </header>

      <div className={styles.statsGrid}>
        <NeoCard className={styles.statCard}>
          <div className={styles.statIcon} style={{ color: 'var(--primary-color)' }}>
            <FileText size={32} />
          </div>
          <div className={styles.statContent}>
            <h3>14</h3>
            <p>Documents Uploaded</p>
          </div>
        </NeoCard>

        <NeoCard className={styles.statCard}>
          <div className={styles.statIcon} style={{ color: 'var(--success)' }}>
            <MessageSquare size={32} />
          </div>
          <div className={styles.statContent}>
            <h3>128</h3>
            <p>Questions Asked</p>
          </div>
        </NeoCard>

        <NeoCard className={styles.statCard}>
          <div className={styles.statIcon} style={{ color: 'var(--warning)' }}>
            <Bot size={32} />
          </div>
          <div className={styles.statContent}>
            <h3>3</h3>
            <p>Active Chats</p>
          </div>
        </NeoCard>

        <NeoCard className={styles.statCard}>
          <div className={styles.statIcon} style={{ color: 'var(--error)' }}>
            <BarChart size={32} />
          </div>
          <div className={styles.statContent}>
            <h3>94%</h3>
            <p>AI Confidence Avg</p>
          </div>
        </NeoCard>
      </div>
      
      <div className={styles.recentActivity}>
        <h2>Recent Activity</h2>
        <NeoCard>
          <p className={styles.placeholderText}>Your recent chat history and document uploads will appear here.</p>
        </NeoCard>
      </div>
    </div>
  );
};
