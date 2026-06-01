import React from 'react';
import { User, Bot } from 'lucide-react';
import styles from './NeoChatBubble.module.css';

interface Source {
  filename: string;
  chunkId: number;
}

interface NeoChatBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  confidence?: number;
  sources?: Source[];
  timestamp: string;
}

export const NeoChatBubble: React.FC<NeoChatBubbleProps> = ({
  role,
  content,
  confidence,
  sources,
  timestamp
}) => {
  const isUser = role === 'user';

  return (
    <div className={`${styles.bubbleWrapper} ${isUser ? styles.userWrapper : styles.aiWrapper}`}>
      {!isUser && (
        <div className={styles.avatar}>
          <Bot size={20} />
        </div>
      )}
      
      <div className={`${styles.bubble} ${isUser ? styles.userBubble : styles.aiBubble}`}>
        <div className={styles.content}>{content}</div>
        
        {!isUser && (confidence || (sources && sources.length > 0)) && (
          <div className={styles.metaData}>
            {confidence && (
              <span className={styles.confidence}>
                Confidence: <strong>{confidence}%</strong>
              </span>
            )}
            {sources && sources.length > 0 && (
              <div className={styles.sourcesList}>
                <span>Sources:</span>
                {sources.map((s, idx) => (
                  <span key={idx} className={styles.sourceTag}>
                    {s.filename} (Ch {s.chunkId})
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
        
        <div className={styles.timestamp}>{timestamp}</div>
      </div>

      {isUser && (
        <div className={`${styles.avatar} ${styles.userAvatar}`}>
          <User size={20} />
        </div>
      )}
    </div>
  );
};
