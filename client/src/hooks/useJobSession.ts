import { useCallback, useEffect, useRef, useState } from 'react';
import { documentService } from '../services/documentService';
import type { EngineResponse, JobAccepted, JobStatus, ProcessingMode } from '../types/api.types';

const STORAGE_KEY = 'mf.active_job';
const POLL_MS = 2000;
const MAX_CONSECUTIVE_ERRORS = 10;

export type SessionPhase =
  | { kind: 'idle' }
  | { kind: 'processing'; job: JobAccepted; chunksDone: number }
  | { kind: 'ready'; data: EngineResponse; file?: File; rawChunks?: string[] }
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

function handleStatusUpdate(
  status: JobStatus,
  activeJob: JobAccepted,
  activeFileRef: React.MutableRefObject<File | null>,
  activeChunksRef: React.MutableRefObject<string[]>,
  setActiveJob: (job: JobAccepted | null) => void,
  setPhase: (phase: SessionPhase) => void,
) {
  if (status.status === 'done' && status.payload && status.classification) {
    const savedFile = activeFileRef.current;
    const rawChunks = status.raw_chunks;
    activeChunksRef.current = rawChunks ?? [];
    window.localStorage.removeItem(STORAGE_KEY);
    setActiveJob(null);
    setPhase({
      kind: 'ready',
      data: {
        classification: status.classification,
        payload: status.payload,
      },
      file: savedFile ?? undefined,
      rawChunks,
    });
  } else if (status.status === 'failed') {
    window.localStorage.removeItem(STORAGE_KEY);
    setActiveJob(null);
    setPhase({ kind: 'failed', message: status.error || 'Processing failed.' });
  } else if (status.chunks_done !== undefined) {
    setPhase({ kind: 'processing', job: activeJob, chunksDone: status.chunks_done });
  }
}

export function useJobSession() {
  const [activeJob, setActiveJob] = useState<JobAccepted | null>(readSavedJob);
  const activeFileRef = useRef<File | null>(null);
  const activeChunksRef = useRef<string[]>([]);
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
    activeChunksRef.current = [];
    window.localStorage.removeItem(STORAGE_KEY);
    setActiveJob(null);
    setPhase({ kind: 'idle' });
  }, []);

  const generateMore = useCallback(async (mode: ProcessingMode, flashcardCount?: number, notesSubtask?: string) => {
    const chunks = activeChunksRef.current;
    if (!chunks.length) return;
    try {
      const job = await documentService.reprocessJob(chunks, mode, flashcardCount, notesSubtask);
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(job));
      setPhase({ kind: 'processing', job, chunksDone: 0 });
      setActiveJob(job);
    } catch {
      // reprocess failed
    }
  }, []);

  const kill = useCallback(async () => {
    const job = activeJob;
    activeFileRef.current = null;
    activeChunksRef.current = [];
    window.localStorage.removeItem(STORAGE_KEY);
    setActiveJob(null);
    setPhase({ kind: 'idle' });
    if (job) {
      try {
        await documentService.cancelJob(job.job_id);
      } catch {
        // engine unreachable or job already terminal
      }
    }
  }, [activeJob]);

  // SSE with polling fallback
  useEffect(() => {
    if (!activeJob) return;

    let cancelled = false;
    let es: EventSource | null = null;
    let pollInterval: ReturnType<typeof setInterval> | null = null;
    let consecutiveErrors = 0;

    const handleEvent = (status: JobStatus) => {
      if (cancelled) return;
      consecutiveErrors = 0;
      handleStatusUpdate(status, activeJob, activeFileRef, activeChunksRef, setActiveJob, setPhase);
    };

    const handlePollError = () => {
      consecutiveErrors += 1;
      if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS && !cancelled) {
        window.localStorage.removeItem(STORAGE_KEY);
        setActiveJob(null);
        setPhase({
          kind: 'failed',
          message: 'Lost connection while processing. The job may still finish server-side — try uploading again.',
        });
      }
    };

    const startPolling = () => {
      if (pollInterval) return;
      const tick = async () => {
        try {
          const status = await documentService.getJob(activeJob.job_id);
          handleEvent(status);
        } catch {
          handlePollError();
        }
      };
      tick();
      pollInterval = setInterval(tick, POLL_MS);
    };

    // try SSE first
    try {
      es = documentService.connectSSE(
        activeJob.job_id,
        handleEvent,
        () => {
          // SSE failed, fall back to polling
          if (!cancelled) startPolling();
        },
      );
    } catch {
      startPolling();
    }

    return () => {
      cancelled = true;
      es?.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [activeJob]);

  return { phase, startJob, reset, kill, generateMore };
}
