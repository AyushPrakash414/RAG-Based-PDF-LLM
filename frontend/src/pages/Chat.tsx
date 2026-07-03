import React, { useState, useEffect, useRef } from 'react';
import { Plus, Send, Paperclip, Shield, Search, Bot as BotIcon, FileText, Database, Trash2 } from 'lucide-react';
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
  status?: string;
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

  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this conversation?')) return;
    
    try {
      await api.delete(`/chat/session/${id}`);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (activeSession === id) {
        setActiveSession(null);
      }
    } catch (err) {
      console.error('Failed to delete session', err);
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
        status: data.status,
        sources: data.sources ? data.sources.map((s: any) => typeof s === 'string' ? { filename: s } : s) : undefined,
        timestamp: data.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, aiMessage]);
      
      // Auto-refresh sessions to get updated title if this was the first message
      if (messages.length === 0) {
        fetchSessions();
      }
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, overflow: 'hidden' }}>
                <MessageSquareIcon />
                <span className={styles.sessionTitle}>{session.title}</span>
              </div>
              <button 
                className={styles.deleteSessionBtn} 
                onClick={(e) => handleDeleteSession(session.id, e)}
                title="Delete Conversation"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
          {sessions.length === 0 && <p style={{ padding: '1rem', color: '#666', fontSize: '0.9rem' }}>No conversations yet.</p>}
        </div>
      </div>

      {/* Center - Chat Area */}
      <div className={styles.centerPanel}>
        {/* Mobile Header (Hidden on Desktop) */}
        <div className={styles.mobileHeader}>
          <select 
            className={styles.mobileSessionSelect} 
            value={activeSession || ''} 
            onChange={(e) => setActiveSession(e.target.value)}
          >
            {sessions.length === 0 && <option value="" disabled>No conversations...</option>}
            {sessions.map(s => (
              <option key={s.id} value={s.id}>{s.title}</option>
            ))}
          </select>
          <button className={styles.mobileNewChatBtn} onClick={handleNewChat} title="New Chat">
            <Plus size={20} />
          </button>
        </div>

        <div className={styles.messagesArea}>
          
          {sessions.length === 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '1rem', color: '#666' }}>
              <MessageSquareIcon />
              <p>Welcome! Start a new conversation to ask questions about your documents.</p>
              <NeoButton onClick={handleNewChat} icon={<Plus size={18} />}>Start New Chat</NeoButton>
            </div>
          )}
          
          {messages.map((msg, index) => {
            const isAi = msg.role.toLowerCase() === 'assistant' || msg.role.toLowerCase() === 'ai';
            const isApproved = msg.status === 'APPROVED';
            return (
            <React.Fragment key={msg.id}>
              {/* Show Status Card only for the latest AI message */}
              {isAi && index === messages.length - 1 && (
                <NeoCard className={styles.statusCard}>
                  <h4>Self-Healing Status</h4>
                  <div className={styles.statusGrid}>
                    <div className={styles.statusItem}>
                      <Search size={16} className={isApproved ? styles.statusIconSuccess : styles.statusIconError} />
                      <span style={{ color: isApproved ? 'inherit' : 'var(--error)' }}>
                        {isApproved ? 'Retrieval Valid' : 'Retrieval Exhausted / Failed'}
                      </span>
                    </div>
                    <div className={styles.statusItem}>
                      <Shield size={16} className={isApproved ? styles.statusIconSuccess : styles.statusIconError} />
                      <span style={{ color: isApproved ? 'inherit' : 'var(--error)' }}>
                        {isApproved ? 'Critic Approved' : 'Critic Rejected'}
                      </span>
                    </div>
                    {msg.confidence !== undefined && (
                      <div className={styles.statusItem}>
                        <BotIcon size={16} className={isApproved ? styles.statusIconSuccess : styles.statusIconError} />
                        <span style={{ color: isApproved ? 'inherit' : 'var(--error)' }}>Confidence {Math.round(msg.confidence * 100)}%</span>
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
            );
          })}
          
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
            {latestAiMessage.confidence !== undefined && (
              <div className={styles.sourceConfidence}>
                Confidence: <strong>{Math.round(latestAiMessage.confidence * 100)}%</strong>
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
