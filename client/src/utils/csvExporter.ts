import type { NotesPayload, PYQAnalysisPayload } from '../types/api.types';
import type { ExportPayload, ExportOptions } from '../types/export';
import { triggerDownload } from './triggerDownload';

export function exportToCsv(payload: ExportPayload, options: ExportOptions): void {
  if (options.docType === 'NOTES') {
    exportFlashcards(payload as NotesPayload, options);
  } else if (options.docType === 'PYQ') {
    exportTopicFrequency(payload as PYQAnalysisPayload, options);
  }
}

function exportFlashcards(payload: NotesPayload, options: ExportOptions): void {
  const filename = options.filename ?? `mindforge-flashcards-${Date.now()}.csv`;
  const header = '"Front","Back","Category"';
  const rows = payload.flashcards.map((fc) => {
    return `"${escapeCsv(fc.front)}","${escapeCsv(fc.back)}","${escapeCsv(fc.bloom_category)}"`;
  });
  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  triggerDownload(blob, filename);
}

function exportTopicFrequency(payload: PYQAnalysisPayload, options: ExportOptions): void {
  const filename = options.filename ?? `mindforge-pyq-topics-${Date.now()}.csv`;
  const header = '"Topic","Percentage","Question Count"';
  const rows = payload.topic_frequency.map((tf) => {
    return `"${escapeCsv(tf.topic)}","${tf.percentage}","${tf.question_count}"`;
  });
  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  triggerDownload(blob, filename);
}

function escapeCsv(field: string): string {
  return field.replace(/"/g, '""');
}
