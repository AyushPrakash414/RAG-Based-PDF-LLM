import React from 'react';
import { FileText, Trash2, Eye } from 'lucide-react';
import { NeoCard } from './NeoCard';
import styles from './NeoDocumentCard.module.css';

interface NeoDocumentCardProps {
  id: string;
  filename: string;
  uploadDate: string;
  chunkCount: number;
  onDelete?: (id: string) => void;
  onView?: (id: string) => void;
}

export const NeoDocumentCard: React.FC<NeoDocumentCardProps> = ({
  id,
  filename,
  uploadDate,
  chunkCount,
  onDelete,
  onView
}) => {
  return (
    <NeoCard className={styles.docCard}>
      <div className={styles.iconWrapper}>
        <FileText size={32} />
      </div>
      
      <div className={styles.docInfo}>
        <h4 className={styles.filename} title={filename}>{filename}</h4>
        <div className={styles.meta}>
          <span>{uploadDate}</span>
          <span>•</span>
          <span>{chunkCount} chunks</span>
        </div>
      </div>
      
      <div className={styles.actions}>
        <button 
          className={`${styles.actionBtn} ${styles.viewBtn}`}
          onClick={() => onView && onView(id)}
          title="View Details"
        >
          <Eye size={18} />
        </button>
        <button 
          className={`${styles.actionBtn} ${styles.deleteBtn}`}
          onClick={() => onDelete && onDelete(id)}
          title="Delete Document"
        >
          <Trash2 size={18} />
        </button>
      </div>
    </NeoCard>
  );
};
