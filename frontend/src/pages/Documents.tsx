import React, { useState, useEffect, useRef } from 'react';
import { Upload, Search, FileText } from 'lucide-react';
import { NeoCard } from '../components/shared/NeoCard';
import { NeoButton } from '../components/shared/NeoButton';
import { NeoInput } from '../components/shared/NeoInput';
import { NeoDocumentCard } from '../components/shared/NeoDocumentCard';
import api from '../api/axios';
import styles from './Documents.module.css';

interface Document {
  id: string;
  fileName: string;
  uploadedAt: string;
}

export const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    try {
      const { data } = await api.get('/documents');
      setDocuments(data);
    } catch (err) {
      console.error('Failed to fetch documents', err);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    setUploading(true);
    setError('');

    try {
      await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      fetchDocuments();
    } catch (err: any) {
      setError(err.response?.data || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

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
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileUpload(file);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileUpload(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/documents/${id}`);
      setDocuments(docs => docs.filter(doc => doc.id !== id));
    } catch (err) {
      console.error('Failed to delete document', err);
    }
  };

  const filteredDocs = documents.filter(doc => 
    doc.fileName?.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
          <input 
            type="file" 
            ref={fileInputRef} 
            style={{ display: 'none' }} 
            onChange={handleFileChange}
            accept=".pdf,.docx,.txt"
          />
          <NeoButton 
            icon={<Upload size={18} />} 
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? 'Uploading...' : 'Upload New'}
          </NeoButton>
        </div>
      </div>

      {error && <div className={styles.errorAlert} style={{ color: 'red', marginBottom: '1rem' }}>{error}</div>}

      <NeoCard 
        className={`${styles.uploadZone} ${isDragging ? styles.dragging : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{ cursor: 'pointer' }}
      >
        <div className={styles.uploadContent}>
          <div className={styles.uploadIconWrapper}>
            <Upload size={48} />
          </div>
          <h3>{uploading ? 'Uploading...' : 'Drop Files Here'}</h3>
          <p>or click to browse from your computer</p>
          <div className={styles.supportedFormats}>
            <span className={styles.formatBadge}>PDF</span>
            <span className={styles.formatBadge}>DOCX</span>
            <span className={styles.formatBadge}>TXT</span>
          </div>
        </div>
      </NeoCard>

      <div className={styles.documentList}>
        <h2>Your Documents ({filteredDocs.length})</h2>
        <div className={styles.grid}>
          {filteredDocs.map((doc) => (
            <NeoDocumentCard
              key={doc.id}
              id={doc.id}
              filename={doc.fileName}
              uploadDate={doc.uploadedAt}
              chunkCount={10}
              onDelete={handleDelete}
              onView={(id) => console.log('View', id)}
            />
          ))}
          {filteredDocs.length === 0 && <p>No documents found.</p>}
        </div>
      </div>
    </div>
  );
};
