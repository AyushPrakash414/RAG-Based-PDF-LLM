import React, { useState } from 'react';
import { Plus, Send, Paperclip, Shield, Search, Bot as BotIcon, FileText, Database } from 'lucide-react';
import { NeoCard } from '../components/shared/NeoCard';
import { NeoButton } from '../components/shared/NeoButton';
import { NeoInput } from '../components/shared/NeoInput';
import { NeoChatBubble } from '../components/shared/NeoChatBubble';
import styles from './Chat.module.css';

// Mock Data
const mockSessions = [
  { id: '1', title: 'Ramayana Research' },
  { id: '2', title: 'Project Notes' },
  { id: '3', title: 'History Notes' },
];

const mockMessages = [
  {
    id: '1',
    role: 'user' as const,
    content: 'What were the key events in the Aranya Kanda of the Ramayana?',
    timestamp: '10:42 AM'
  },
  {
    id: '2',
    role: 'assistant' as const,
    content: 'The Aranya Kanda (The Book of the Forest) is the third book of the Ramayana. Key events include:\n\n1. Rama, Sita, and Lakshmana journey deeper into the Dandaka forest.\n2. The encounter with the demoness Surpanakha, whose nose is cut off by Lakshmana.\n3. The demon king Ravana abducts Sita with the help of Maricha, who takes the form of a golden deer.\n4. Rama and Lakshmana discover the dying vulture Jatayu, who fought Ravana to save Sita.',
    confidence: 94,
    sources: [
      { filename: 'ramayana.txt', chunkId: 12 },
      { filename: 'ramayana.txt', chunkId: 14 }
    ],
    timestamp: '10:43 AM'
  }
];

export const Chat: React.FC = () => {
  const [input, setInput] = useState('');
  const [activeSession, setActiveSession] = useState('1');

  return (
    <div className={styles.chatContainer}>
      
      {/* Left Sidebar - Chat Sessions */}
      <div className={styles.leftPanel}>
        <NeoButton fullWidth icon={<Plus size={18} />} className={styles.newChatBtn}>
          New Chat
        </NeoButton>
        <div className={styles.sessionList}>
          {mockSessions.map((session) => (
            <div 
              key={session.id} 
              className={`${styles.sessionItem} ${activeSession === session.id ? styles.activeSession : ''}`}
              onClick={() => setActiveSession(session.id)}
            >
              <MessageSquareIcon />
              <span className={styles.sessionTitle}>{session.title}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Center - Chat Area */}
      <div className={styles.centerPanel}>
        <div className={styles.messagesArea}>
          {/* Self-Healing Status Card - Shown before the latest AI message */}
          <NeoCard className={styles.statusCard}>
            <h4>Self-Healing Status</h4>
            <div className={styles.statusGrid}>
              <div className={styles.statusItem}>
                <Search size={16} className={styles.statusIconSuccess} />
                <span>Retrieval Valid</span>
              </div>
              <div className={styles.statusItem}>
                <Shield size={16} className={styles.statusIconSuccess} />
                <span>Critic Approved</span>
              </div>
              <div className={styles.statusItem}>
                <BotIcon size={16} className={styles.statusIconSuccess} />
                <span>Confidence 94%</span>
              </div>
            </div>
          </NeoCard>

          {mockMessages.map((msg) => (
            <NeoChatBubble
              key={msg.id}
              role={msg.role}
              content={msg.content}
              confidence={msg.confidence}
              sources={msg.sources}
              timestamp={msg.timestamp}
            />
          ))}
        </div>

        <div className={styles.inputArea}>
          <div className={styles.inputWrapper}>
            <button className={styles.attachBtn} title="Attach Document">
              <Paperclip size={20} />
            </button>
            <textarea 
              className={styles.chatInput} 
              placeholder="Ask a question about your documents..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              rows={1}
            />
            <button className={styles.sendBtn} title="Send Message">
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Sources Panel */}
      <div className={styles.rightPanel}>
        <h3>Sources Panel</h3>
        <p className={styles.sourcesDesc}>Documents referenced in the current answer.</p>
        
        <NeoCard className={styles.sourceCard}>
          <div className={styles.sourceHeader}>
            <FileText size={18} />
            <span className={styles.sourceFilename}>ramayana.txt</span>
          </div>
          <div className={styles.sourceChunks}>
            <div className={styles.chunkTag}>
              <Database size={12} /> Chunk 12
            </div>
            <div className={styles.chunkTag}>
              <Database size={12} /> Chunk 14
            </div>
          </div>
          <div className={styles.sourceConfidence}>
            Confidence: <strong>94%</strong>
          </div>
        </NeoCard>
      </div>

    </div>
  );
};

const MessageSquareIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
  </svg>
);
