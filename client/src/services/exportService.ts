import type { ExportPayload, ExportOptions } from '../types/export';
import { exportToJson } from '../utils/jsonExporter';
import { exportToCsv } from '../utils/csvExporter';
import { exportToPdf } from '../utils/pdfExporter';

export function exportStudyAssets(payload: ExportPayload, options: ExportOptions): void {
  switch (options.format) {
    case 'json':
      exportToJson(payload, options);
      break;
    case 'csv':
      if (options.docType !== 'NOTES' && options.docType !== 'PYQ') {
        throw new Error('CSV export is only available for NOTES and PYQ');
      }
      exportToCsv(payload, options);
      break;
    case 'pdf':
      exportToPdf(payload, options);
      break;
  }
}
