import type { JobAccepted, JobStatus, ProcessingMode } from "../types/api.types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
const ENGINE_URL = import.meta.env.VITE_ENGINE_URL || "http://localhost:8000";

export class DocumentUploadError extends Error {
  public readonly code: string;

  constructor(message: string, code: string) {
    super(message);
    this.name = "DocumentUploadError";
    this.code = code;
  }
}

async function errorFrom(response: Response): Promise<DocumentUploadError> {
  const data = await response.json().catch(() => ({}));
  const code = data.error || `HTTP_${response.status}`;
  let message = data.message || "An unknown error occurred.";
  if (response.status === 413 && code === "ERR_413_FILE_TOO_LARGE") {
    message = "File is too large. Maximum size is 15MB.";
  } else if (response.status === 429) {
    message = "Too many requests. Please try again later.";
  } else if (response.status === 503 || code === "ERR_503") {
    message = "MindForge AI engine is currently offline. Please try again later.";
  }
  return new DocumentUploadError(message, code);
}

export const documentService = {
  async processDocument(file: File, mode: ProcessingMode, flashcardCount?: number): Promise<JobAccepted> {
    const params = new URLSearchParams({ mode });
    if (mode === 'notes' && flashcardCount) {
      params.set("flashcard_count", String(flashcardCount));
      params.set("notes_subtask", "flashcards");
    }

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_URL}/api/document/process?${params}`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw await errorFrom(response);
    }

    return response.json();
  },

  async processMultipleDocs(files: File[], mode: ProcessingMode): Promise<JobAccepted> {
    const params = new URLSearchParams({ mode });
    const formData = new FormData();
    for (const f of files) formData.append("files", f);

    const response = await fetch(`${API_URL}/api/document/process?${params}`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw await errorFrom(response);
    }

    return response.json();
  },

  async reprocessJob(
    chunks: string[],
    mode: ProcessingMode,
    flashcardCount?: number,
    notesSubtask?: string,
  ): Promise<JobAccepted> {
    const params = new URLSearchParams({ mode });
    if (mode === 'notes' && flashcardCount) {
      params.set("flashcard_count", String(flashcardCount));
    }
    if (notesSubtask) {
      params.set("notes_subtask", notesSubtask);
    }

    const response = await fetch(`${API_URL}/api/document/reprocess?${params}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chunks }),
    });

    if (!response.ok) {
      throw await errorFrom(response);
    }

    return response.json();
  },

  async getJob(jobId: string): Promise<JobStatus> {
    const response = await fetch(`${API_URL}/api/jobs/${jobId}`);
    if (!response.ok) {
      throw await errorFrom(response);
    }
    return response.json();
  },

  async cancelJob(jobId: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/jobs/${jobId}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      throw await errorFrom(response);
    }
  },

  connectSSE(jobId: string, onEvent: (data: JobStatus) => void, onError: () => void): EventSource {
    const es = new EventSource(`${ENGINE_URL}/api/v1/jobs/${jobId}/stream`);
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as JobStatus;
        onEvent(data);
      } catch {
        onError();
      }
    };
    es.onerror = () => {
      onError();
      es.close();
    };
    return es;
  },
};
