import React, { useState, useEffect, useRef } from 'react';
import { Search, Database, Shield, Bot, Sparkles, CheckCircle } from 'lucide-react';
import styles from './AIThinkingTimeline.module.css';

const STAGES = [
  { icon: Search,      label: 'Searching Documents...',       completedLabel: 'Documents Searched' },
  { icon: Database,    label: 'Retrieving Relevant Chunks...', completedLabel: 'Chunks Retrieved' },
  { icon: Shield,      label: 'Validating Context...',         completedLabel: 'Context Validated' },
  { icon: Bot,         label: 'Generating Response...',        completedLabel: 'Response Generated' },
  { icon: Sparkles,    label: 'Checking for Hallucinations...', completedLabel: 'Hallucination Check Passed' },
  { icon: CheckCircle, label: 'Preparing Sources...',          completedLabel: 'Sources Ready' },
];

const STEP_INTERVAL = 1800; // ms between each step completing

export const AIThinkingTimeline: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const stepsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setActiveStep(prev => {
        if (prev >= STAGES.length - 1) {
          // Stay on the last step (don't loop)
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

  // Calculate connector fill height
  const connectorHeight = stepsRef.current
    ? (activeStep / (STAGES.length - 1)) * 100
    : 0;

  return (
    <div className={styles.timeline} role="status" aria-label="AI is processing your question">
      <div className={styles.timelineHeader}>
        <div className={styles.headerDot} />
        Self-Healing RAG Pipeline
      </div>

      <div className={styles.steps} ref={stepsRef}>
        {/* Connector fill line */}
        <div
          className={styles.connectorFill}
          style={{ height: `${connectorHeight}%` }}
        />

        {STAGES.map((stage, i) => {
          const Icon = stage.icon;
          let state = 'stepPending';
          if (i < activeStep) state = 'stepCompleted';
          else if (i === activeStep) state = 'stepActive';

          return (
            <div
              key={i}
              className={`${styles.step} ${styles[state]}`}
              style={{ animationDelay: `${i * 0.2}s` }}
            >
              <div className={styles.stepIcon}>
                {i < activeStep ? (
                  <CheckCircle size={14} />
                ) : (
                  <Icon size={14} />
                )}
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
