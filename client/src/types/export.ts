import type { DocType, SyllabusPayload, PYQAnalysisPayload, NotesPayload } from './api.types';

export type ExportFormat = 'json' | 'csv' | 'pdf';

export type ExportPayload = SyllabusPayload | PYQAnalysisPayload | NotesPayload;

export interface ExportOptions {
  format: ExportFormat;
  docType: DocType;
  filename?: string;
}
