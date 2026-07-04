import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, Scissors, Cpu, Database, CheckCircle } from 'lucide-react';
import styles from './UploadSkeleton.module.css';

const STAGES = [
  { icon: Upload,      label: 'Uploading File...',         completedLabel: 'File Uploaded' },
  { icon: FileText,    label: 'Extracting Text...',        completedLabel: 'Text Extracted' },
  { icon: Scissors,    label: 'Chunking Document...',      completedLabel: 'Document Chunked' },
  { icon: Cpu,         label: 'Generating Embeddings...',  completedLabel: 'Embeddings Generated' },
  { icon: Database,    label: 'Storing in Vector DB...',   completedLabel: 'Stored in Qdrant' },
  { icon: CheckCircle, label: 'Finalizing...',             completedLabel: 'Complete!' },
];

const STEP_INTERVAL = 2200;

export const UploadSkeleton: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setActiveStep(prev => {
        if (prev >= STAGES.length - 1) {
          if (intervalRef.current) clearInterval(intervalRef.current);
          return prev;
        }
        return prev + 1;
      });
    }, STEP_INTERVAL);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const progress = ((activeStep + 1) / STAGES.length) * 100;

  return (
    <div className={styles.timeline} role="status" aria-label="Document upload in progress">
      <div className={styles.timelineHeader}>
        <Upload size={16} />
        Processing Document
      </div>

      <div className={styles.progressBar}>
        <div className={styles.progressFill} style={{ width: `${progress}%` }} />
      </div>

      <div className={styles.steps}>
        <div
          className={styles.connectorFill}
          style={{ height: `${(activeStep / (STAGES.length - 1)) * 100}%` }}
        />
        {STAGES.map((stage, i) => {
          const Icon = stage.icon;
          let state = 'stepPending';
          if (i < activeStep) state = 'stepCompleted';
          else if (i === activeStep) state = 'stepActive';

          return (
            <div key={i} className={`${styles.step} ${styles[state]}`}>
              <div className={styles.stepIcon}>
                {i < activeStep ? <CheckCircle size={12} /> : <Icon size={12} />}
              </div>
              <span className={styles.stepLabel}>
                {i < activeStep ? stage.completedLabel : stage.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
