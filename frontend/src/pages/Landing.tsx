import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, FileText, Shield, Rocket, GitBranch, ChevronRight } from 'lucide-react';
import { NeoButton } from '../components/shared/NeoButton';
import { NeoCard } from '../components/shared/NeoCard';
import styles from './Landing.module.css';

export const Landing: React.FC = () => {
  return (
    <div className={styles.landingContainer}>
      <nav className={styles.navbar}>
        <div className={styles.navLeft}>
          <Bot size={28} />
          <span className={styles.logo}>Self-Healing RAG</span>
        </div>
        <div className={styles.navRight}>
          <Link to="/login" className={styles.navLink}>Login</Link>
          <Link to="/register">
            <NeoButton variant="primary">Get Started</NeoButton>
          </Link>
        </div>
      </nav>

      <main className={styles.main}>
        <section className={styles.hero}>
          <h1>Chat With Your Documents Using Self-Healing AI</h1>
          <p>Upload documents. Ask questions. Get grounded answers with source citations.</p>
          <div className={styles.heroActions}>
            <Link to="/register">
              <NeoButton icon={<Rocket size={18} />}>Get Started</NeoButton>
            </Link>
            <a href="https://github.com/AyushPrakash414/RAG-Based-PDF-LLM" target="_blank" rel="noreferrer">
              <NeoButton variant="secondary" icon={<GitBranch size={18} />}>View GitHub</NeoButton>
            </a>
          </div>
        </section>

        <section className={styles.features}>
          <NeoCard className={styles.featureCard}>
            <FileText size={32} className={styles.featureIcon} />
            <h3>Document Intelligence</h3>
            <p>Upload PDFs, DOCX, TXT and chat with them.</p>
          </NeoCard>
          
          <NeoCard className={styles.featureCard}>
            <Bot size={32} className={styles.featureIcon} />
            <h3>Self-Healing RAG</h3>
            <p>Retrieval Validator + Critic Agent + Query Rewriter.</p>
          </NeoCard>
          
          <NeoCard className={styles.featureCard}>
            <Shield size={32} className={styles.featureIcon} />
            <h3>Reliable Answers</h3>
            <p>Grounded responses with source citations.</p>
          </NeoCard>
        </section>

        <section className={styles.architecture}>
          <h2>How It Works</h2>
          <div className={styles.flowContainer}>
            <NeoCard className={styles.flowStep}>Upload Document</NeoCard>
            <ChevronRight size={24} className={styles.arrow} />
            <NeoCard className={styles.flowStep}>Spring Boot</NeoCard>
            <ChevronRight size={24} className={styles.arrow} />
            <NeoCard className={styles.flowStep}>Self-Healing RAG</NeoCard>
            <ChevronRight size={24} className={styles.arrow} />
            <NeoCard className={styles.flowStep}>Qdrant + Groq</NeoCard>
          </div>
        </section>
      </main>

      <footer className={styles.footer}>
        <p>© 2026 Self-Healing RAG Platform. Neo-Brutalist Design.</p>
      </footer>
    </div>
  );
};
