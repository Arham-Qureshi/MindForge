import { useState } from 'react';
import type { EngineResponse, UploadStatus } from '../../../types/api.types';
import { documentService, DocumentUploadError } from '../../../services/documentService';

const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15MB

export function useFileUpload() {
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EngineResponse | null>(null);

  const reset = () => {
    setStatus('idle');
    setStatusMessage('');
    setError(null);
    setResult(null);
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
    reset();
    
    setStatus('validating');
    setStatusMessage('Checking file...');
    
    const validationError = validateFile(file);
    if (validationError) {
      setStatus('error');
      setError(validationError);
      return;
    }

    try {
      setStatus('uploading');
      setStatusMessage('Uploading to MindForge...');
      
      // In a real app with progress events, we might use XMLHttpRequest here,
      // but fetch doesn't support upload progress natively yet.
      // We rely on the backend proxying, so we'll simulate the inner stages if the request is fast,
      // or we could listen to a WebSocket. For this feature, we await the full HTTP response.
      // We update the status message to indicate processing once uploaded.
      
      setStatus('classifying');
      setStatusMessage('Running heuristic classification...');
      
      // We simulate the backend stages since we only have a single endpoint that blocks until done.
      const interval = setInterval(() => {
        setStatus(prev => {
          if (prev === 'classifying') {
            setStatusMessage('Extracting study assets...');
            return 'extracting';
          }
          return prev;
        });
      }, 3000); // Shift to extracting after 3s

      const response = await documentService.processDocument(file);
      
      clearInterval(interval);
      
      setResult(response);
      setStatus('done');
      setStatusMessage('Processing complete!');
      
    } catch (err) {
      setStatus('error');
      if (err instanceof DocumentUploadError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred.');
      }
    }
  };

  return {
    status,
    statusMessage,
    error,
    result,
    upload,
    reset
  };
}
