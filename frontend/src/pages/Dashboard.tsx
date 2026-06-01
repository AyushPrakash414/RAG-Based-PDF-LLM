import React, { useState, useEffect } from 'react';
import { FileText, MessageSquare, Bot, BarChart } from 'lucide-react';
import { NeoCard } from '../components/shared/NeoCard';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import styles from './Dashboard.module.css';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [docCount, setDocCount] = useState(0);
  const [chatCount, setChatCount] = useState(0);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [docsRes, chatsRes] = await Promise.all([
          api.get('/documents'),
          api.get('/chat/session')
        ]);
        setDocCount(docsRes.data.length || 0);
        setChatCount(chatsRes.data.length || 0);
      } catch (error) {
        console.error('Failed to fetch dashboard stats', error);
      }
    };
    fetchStats();
  }, []);

  return (
    <div className={styles.dashboardContainer}>
      <header className={styles.header}>
        <h1>Welcome, {user?.name?.split(' ')[0] || 'User'}!</h1>
        <p>Here is an overview of your activity.</p>
      </header>

      <div className={styles.statsGrid}>
        <NeoCard className={styles.statCard}>
          <div className={styles.statIcon} style={{ color: 'var(--primary-color)' }}>
            <FileText size={32} />
          </div>
          <div className={styles.statContent}>
            <h3>{docCount}</h3>
            <p>Documents Uploaded</p>
          </div>
        </NeoCard>

        <NeoCard className={styles.statCard}>
          <div className={styles.statIcon} style={{ color: 'var(--success)' }}>
            <MessageSquare size={32} />
          </div>
          <div className={styles.statContent}>
            <h3>0</h3>
            <p>Questions Asked</p>
          </div>
        </NeoCard>

        <NeoCard className={styles.statCard}>
          <div className={styles.statIcon} style={{ color: 'var(--warning)' }}>
            <Bot size={32} />
          </div>
          <div className={styles.statContent}>
            <h3>{chatCount}</h3>
            <p>Active Chats</p>
          </div>
        </NeoCard>

        <NeoCard className={styles.statCard}>
          <div className={styles.statIcon} style={{ color: 'var(--error)' }}>
            <BarChart size={32} />
          </div>
          <div className={styles.statContent}>
            <h3>0%</h3>
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
