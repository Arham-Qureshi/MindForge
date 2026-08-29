import { useState } from 'react';
import type { JobAccepted, ProcessingMode, UploadStatus } from '../../../types/api.types';
import { documentService, DocumentUploadError } from '../../../services/documentService';

const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15MB

export type UseFileUploadOptions = {
  onAccepted?: (job: JobAccepted, file: File) => void;
  mode: ProcessingMode;
  flashcardCount?: number;
};

export function useFileUpload({ onAccepted, mode, flashcardCount }: UseFileUploadOptions) {
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setStatus('idle');
    setError(null);
  };

  const validateFile = (file: File): string | null => {
    if (file.type !== 'application/pdf') {
      return 'Only PDF files are accepted.';
    }
    if (file.size > MAX_FILE_SIZE) {
      return 'File is too large. Maximum size is 15MB.';
    }
    return null;
  };

  const upload = async (file: File) => {
    setStatus('uploading');
    setError(null);

    const validationError = validateFile(file);
    if (validationError) {
      setStatus('error');
      setError(validationError);
      return;
    }

    try {
      // engine replies 202 fast; chunk progress arrives via job polling
      const job = await documentService.processDocument(file, mode, flashcardCount);
      if (onAccepted) onAccepted(job, file);
    } catch (err) {
      setStatus('error');
      if (err instanceof DocumentUploadError || err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred.');
      }
    }
  };

  const uploadMultiple = async (files: File[]) => {
    setStatus('uploading');
    setError(null);
    for (const f of files) {
      const e = validateFile(f);
      if (e) {
        setStatus('error');
        setError(e);
        return;
      }
    }
    try {
      const job = await documentService.processMultipleDocs(files, mode);
      if (onAccepted && files[0]) onAccepted(job, files[0]);
    } catch (err) {
      setStatus('error');
      if (err instanceof DocumentUploadError || err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred.');
      }
    }
  };

  return { status, error, upload, uploadMultiple, reset };
}
