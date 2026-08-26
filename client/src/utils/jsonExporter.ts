import type { ExportPayload, ExportOptions } from '../types/export';
import { triggerDownload } from './triggerDownload';

export function exportToJson(payload: ExportPayload, options: ExportOptions): void {
  const filename = options.filename ?? `mindforge-${options.docType.toLowerCase()}-${Date.now()}.json`;
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  triggerDownload(blob, filename);
}
