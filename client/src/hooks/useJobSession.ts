import { useCallback, useEffect, useRef, useState } from 'react';
import { documentService } from '../services/documentService';
import type { EngineResponse, JobAccepted, ProcessingMode } from '../types/api.types';

const STORAGE_KEY = 'mf.active_job';
const POLL_MS = 2000;
const MAX_CONSECUTIVE_ERRORS = 10; // ~20s of dead gateway before we give up

export type SessionPhase =
  | { kind: 'idle' }
  | { kind: 'processing'; job: JobAccepted; chunksDone: number }
  | { kind: 'ready'; data: EngineResponse; file?: File }
  | { kind: 'failed'; message: string };

function readSavedJob(): JobAccepted | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const saved = JSON.parse(raw) as JobAccepted;
    if (saved?.job_id && saved?.chunks_total) return saved;
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
  }
  return null;
}

export function useJobSession() {
  const [activeJob, setActiveJob] = useState<JobAccepted | null>(readSavedJob);
  const activeFileRef = useRef<File | null>(null);
  const [phase, setPhase] = useState<SessionPhase>(() => {
    const saved = readSavedJob();
    return saved ? { kind: 'processing', job: saved, chunksDone: 0 } : { kind: 'idle' };
  });

  const startJob = useCallback((job: JobAccepted, file?: File) => {
    activeFileRef.current = file ?? null;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(job));
    setPhase({ kind: 'processing', job, chunksDone: 0 });
    setActiveJob(job);
  }, []);

  const reset = useCallback(() => {
    activeFileRef.current = null;
    window.localStorage.removeItem(STORAGE_KEY);
    setActiveJob(null);
    setPhase({ kind: 'idle' });
  }, []);

  const generateMore = useCallback(async (mode: ProcessingMode, flashcardCount?: number) => {
    const file = activeFileRef.current;
    if (!file) return;
    try {
      const job = await documentService.processDocument(file, mode, flashcardCount);
      activeFileRef.current = file;
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(job));
      setPhase({ kind: 'processing', job, chunksDone: 0 });
      setActiveJob(job);
    } catch {
      // upload failed — keep current phase, caller can handle via upload error state
    }
  }, []);

  // stop polling instantly, clear the session, then best-effort cancel server-side
  // so the engine stops burning provider quota on an abandoned job
  const kill = useCallback(async () => {
    const job = activeJob;
    activeFileRef.current = null;
    window.localStorage.removeItem(STORAGE_KEY);
    setActiveJob(null);
    setPhase({ kind: 'idle' });
    if (job) {
      try {
        await documentService.cancelJob(job.job_id);
      } catch {
        // engine unreachable or job already terminal; local session is cleared either way
      }
    }
  }, [activeJob]);

  useEffect(() => {
    if (!activeJob) return;

    let cancelled = false;
    let consecutiveErrors = 0;
    const tick = async () => {
      try {
        const status = await documentService.getJob(activeJob.job_id);
        if (cancelled) return;
        consecutiveErrors = 0;

        if (status.status === 'done' && status.payload && status.classification) {
          const savedFile = activeFileRef.current;
          window.localStorage.removeItem(STORAGE_KEY);
          setActiveJob(null);
          setPhase({
            kind: 'ready',
            data: {
              classification: status.classification,
              payload: status.payload,
            },
            file: savedFile ?? undefined,
          });
        } else if (status.status === 'failed') {
          window.localStorage.removeItem(STORAGE_KEY);
          setActiveJob(null);
          setPhase({ kind: 'failed', message: status.error || 'Processing failed.' });
        } else if (status.chunks_done !== undefined) {
          setPhase({ kind: 'processing', job: activeJob, chunksDone: status.chunks_done });
        }
      } catch {
        // transient network/gateway errors: keep polling for a while, then surface
        consecutiveErrors += 1;
        if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS && !cancelled) {
          window.localStorage.removeItem(STORAGE_KEY);
          setActiveJob(null);
          setPhase({
            kind: 'failed',
            message:
              'Lost connection while processing. The job may still finish server-side — try uploading again.',
          });
        }
      }
    };

    tick();
    const interval = setInterval(tick, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [activeJob]);

  return { phase, startJob, reset, kill, generateMore };
}
