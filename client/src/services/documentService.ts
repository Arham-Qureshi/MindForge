import type { EngineResponse } from "../types/api.types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export class DocumentUploadError extends Error {
  public readonly code: string;
  
  constructor(message: string, code: string) {
    super(message);
    this.name = "DocumentUploadError";
    this.code = code;
  }
}

export const documentService = {
  async processDocument(file: File): Promise<EngineResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_URL}/api/document/process`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      const code = data.error || `HTTP_${response.status}`;
      let message = data.message || "An unknown error occurred during upload.";

      // Map specific backend errors
      if (response.status === 413) {
        message = "File is too large. Maximum size is 15MB.";
      } else if (response.status === 429) {
        message = "Too many requests. Please try again later.";
      } else if (response.status === 503 || code === "ERR_503") {
        message = "MindForge AI engine is currently offline. Please try again later.";
      }

      throw new DocumentUploadError(message, code);
    }

    const data: EngineResponse = await response.json();
    return data;
  },
};
