import React, { useState } from 'react';
import { Upload, Search, FileText } from 'lucide-react';
import { NeoCard } from '../components/shared/NeoCard';
import { NeoButton } from '../components/shared/NeoButton';
import { NeoInput } from '../components/shared/NeoInput';
import { NeoDocumentCard } from '../components/shared/NeoDocumentCard';
import styles from './Documents.module.css';

// Mock data for UI presentation since we haven't built the real API integration yet
const mockDocuments = [
  { id: '1', filename: 'Q3_Financial_Report.pdf', uploadDate: 'Oct 24, 2026', chunkCount: 142 },
  { id: '2', filename: 'Project_Alpha_Architecture.docx', uploadDate: 'Oct 22, 2026', chunkCount: 56 },
  { id: '3', filename: 'meeting_notes_q4.txt', uploadDate: 'Oct 20, 2026', chunkCount: 12 },
];

export const Documents: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    // In a real app, handle file processing here
  };

  return (
    <div className={styles.docsContainer}>
      <div className={styles.header}>
        <div>
          <h1>Documents</h1>
          <p>Manage your knowledge base</p>
        </div>
        
        <div className={styles.headerActions}>
          <div className={styles.searchBox}>
            <NeoInput 
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              icon={<Search size={18} />}
            />
          </div>
          <NeoButton icon={<Upload size={18} />}>Upload New</NeoButton>
        </div>
      </div>

      <NeoCard 
        className={`${styles.uploadZone} ${isDragging ? styles.dragging : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className={styles.uploadContent}>
          <div className={styles.uploadIconWrapper}>
            <Upload size={48} />
          </div>
          <h3>Drop Files Here</h3>
          <p>or click to browse from your computer</p>
          <div className={styles.supportedFormats}>
            <span className={styles.formatBadge}>PDF</span>
            <span className={styles.formatBadge}>DOCX</span>
            <span className={styles.formatBadge}>TXT</span>
          </div>
        </div>
      </NeoCard>

      <div className={styles.documentList}>
        <h2>Your Documents ({mockDocuments.length})</h2>
        <div className={styles.grid}>
          {mockDocuments.map((doc) => (
            <NeoDocumentCard
              key={doc.id}
              id={doc.id}
              filename={doc.filename}
              uploadDate={doc.uploadDate}
              chunkCount={doc.chunkCount}
              onDelete={(id) => console.log('Delete', id)}
              onView={(id) => console.log('View', id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
};
