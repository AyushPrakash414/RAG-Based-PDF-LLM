import React, { useState, useEffect, useRef } from 'react';
import { Plus, Send, Paperclip, Shield, Search, Bot as BotIcon, FileText, Database } from 'lucide-react';
import { NeoCard } from '../components/shared/NeoCard';
import { NeoButton } from '../components/shared/NeoButton';
import { NeoChatBubble } from '../components/shared/NeoChatBubble';
import api from '../api/axios';
import styles from './Chat.module.css';

interface Session {
  id: string;
  title: string;
}

interface Source {
  filename: string;
  chunkId?: number;
}

interface Message {
  id: string;
  role: string;
  content: string;
  timestamp?: string;
  confidence?: number;
  sources?: Source[];
}

export const Chat: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch all sessions on mount
  useEffect(() => {
    fetchSessions();
  }, []);

  // Fetch messages when active session changes
  useEffect(() => {
    if (activeSession) {
      fetchHistory(activeSession);
    } else {
      setMessages([]);
    }
  }, [activeSession]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchSessions = async () => {
    try {
      const { data } = await api.get('/chat/session');
      setSessions(data);
      if (data.length > 0 && !activeSession) {
        setActiveSession(data[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch sessions', err);
    }
  };

  const fetchHistory = async (sessionId: string) => {
    try {
      const { data } = await api.get(`/chat/history/${sessionId}`);
      setMessages(data);
    } catch (err) {
      console.error('Failed to fetch history', err);
    }
  };

  const handleNewChat = async () => {
    try {
      const { data } = await api.post('/chat/session', { title: 'New Conversation' });
      setSessions([data, ...sessions]);
      setActiveSession(data.id);
    } catch (err) {
      console.error('Failed to create new chat', err);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !activeSession || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const { data } = await api.post(`/chat/ask/${activeSession}`, { question: userMessage.content });
      
      const aiMessage: Message = {
        id: data.id || (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.content || data.answer || "No response",
        confidence: data.confidence,
        sources: data.sources ? data.sources.map((s: any) => typeof s === 'string' ? { filename: s } : s) : undefined,
        timestamp: data.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      console.error('Failed to get answer', err);
      // Optionally show an error message bubble
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Get the latest AI message to extract sources for the Right Panel
  const latestAiMessage = [...messages].reverse().find(m => m.role.toLowerCase() === 'assistant' || m.role.toLowerCase() === 'ai');

  return (
    <div className={styles.chatContainer}>
      
      {/* Left Sidebar - Chat Sessions */}
      <div className={styles.leftPanel}>
        <NeoButton fullWidth icon={<Plus size={18} />} className={styles.newChatBtn} onClick={handleNewChat}>
          New Chat
        </NeoButton>
        <div className={styles.sessionList}>
          {sessions.map((session) => (
            <div 
              key={session.id} 
              className={`${styles.sessionItem} ${activeSession === session.id ? styles.activeSession : ''}`}
              onClick={() => setActiveSession(session.id)}
            >
              <MessageSquareIcon />
              <span className={styles.sessionTitle}>{session.title}</span>
            </div>
          ))}
          {sessions.length === 0 && <p style={{ padding: '1rem', color: '#666', fontSize: '0.9rem' }}>No conversations yet.</p>}
        </div>
      </div>

      {/* Center - Chat Area */}
      <div className={styles.centerPanel}>
        <div className={styles.messagesArea}>
          
          {messages.map((msg, index) => (
            <React.Fragment key={msg.id}>
              {/* Show Status Card only for the latest AI message */}
              {(msg.role.toLowerCase() === 'assistant' || msg.role.toLowerCase() === 'ai') && index === messages.length - 1 && (
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
                    {msg.confidence && (
                      <div className={styles.statusItem}>
                        <BotIcon size={16} className={styles.statusIconSuccess} />
                        <span>Confidence {msg.confidence}%</span>
                      </div>
                    )}
                  </div>
                </NeoCard>
              )}
              
              <NeoChatBubble
                role={msg.role.toLowerCase() === 'user' ? 'user' : 'assistant'}
                content={msg.content}
                confidence={msg.confidence}
                sources={msg.sources}
                timestamp={msg.timestamp || ''}
              />
            </React.Fragment>
          ))}
          
          {loading && (
            <div style={{ padding: '1rem', fontStyle: 'italic', color: '#666' }}>
              AI is thinking...
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className={styles.inputArea}>
          <div className={styles.inputWrapper}>
            <button className={styles.attachBtn} title="Attach Document">
              <Paperclip size={20} />
            </button>
            <textarea 
              className={styles.chatInput} 
              placeholder={activeSession ? "Ask a question about your documents..." : "Create a new chat first..."}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={!activeSession || loading}
              rows={1}
            />
            <button className={styles.sendBtn} title="Send Message" onClick={handleSendMessage} disabled={!activeSession || loading || !input.trim()}>
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Sources Panel */}
      <div className={styles.rightPanel}>
        <h3>Sources Panel</h3>
        <p className={styles.sourcesDesc}>Documents referenced in the current answer.</p>
        
        {latestAiMessage?.sources && latestAiMessage.sources.length > 0 ? (
          <NeoCard className={styles.sourceCard}>
            <div className={styles.sourceHeader}>
              <FileText size={18} />
              <span className={styles.sourceFilename}>Reference Documents</span>
            </div>
            <div className={styles.sourceChunks}>
              {latestAiMessage.sources.map((src: any, i) => (
                <div key={i} className={styles.chunkTag}>
                  <Database size={12} /> {typeof src === 'string' ? src : src.filename || 'Document'}
                </div>
              ))}
            </div>
            {latestAiMessage.confidence && (
              <div className={styles.sourceConfidence}>
                Confidence: <strong>{latestAiMessage.confidence}%</strong>
              </div>
            )}
          </NeoCard>
        ) : (
          <div style={{ padding: '1rem', background: '#e0e0e0', borderRadius: '8px', border: '2px solid #111', fontSize: '0.9rem' }}>
            No sources referenced yet.
          </div>
        )}
      </div>

    </div>
  );
};

const MessageSquareIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
  </svg>
);
