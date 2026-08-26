import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { exportStudyAssets } from './exportService';
import * as jsonExporter from '../utils/jsonExporter';
import * as csvExporter from '../utils/csvExporter';
import * as pdfExporter from '../utils/pdfExporter';
import type { SyllabusPayload, NotesPayload, PYQAnalysisPayload } from '../types/api.types';

describe('exportStudyAssets', () => {
  beforeEach(() => {
    vi.spyOn(jsonExporter, 'exportToJson').mockImplementation(() => {});
    vi.spyOn(csvExporter, 'exportToCsv').mockImplementation(() => {});
    vi.spyOn(pdfExporter, 'exportToPdf').mockImplementation(() => {});
  });

  afterEach(() => vi.restoreAllMocks());

  it('routes SYLLABUS to jsonExporter', () => {
    const payload: SyllabusPayload = { course_title: 'X', total_units: 1, learning_path: [], priority_topics: [] };
    exportStudyAssets(payload, { format: 'json', docType: 'SYLLABUS' });
    expect(jsonExporter.exportToJson).toHaveBeenCalledWith(payload, expect.any(Object));
  });

  it('routes PYQ json to jsonExporter', () => {
    const payload: PYQAnalysisPayload = { topic_frequency: [], predicted_questions: [] };
    exportStudyAssets(payload, { format: 'json', docType: 'PYQ' });
    expect(jsonExporter.exportToJson).toHaveBeenCalledWith(payload, expect.any(Object));
  });

  it('routes PYQ csv to csvExporter', () => {
    const payload: PYQAnalysisPayload = { topic_frequency: [], predicted_questions: [] };
    exportStudyAssets(payload, { format: 'csv', docType: 'PYQ' });
    expect(csvExporter.exportToCsv).toHaveBeenCalledWith(payload, expect.any(Object));
  });

  it('routes NOTES flashcards to csvExporter', () => {
    const payload: NotesPayload = { document_summary: '', flashcards: [], practice_exam: [] };
    exportStudyAssets(payload, { format: 'csv', docType: 'NOTES' });
    expect(csvExporter.exportToCsv).toHaveBeenCalledWith(payload, expect.any(Object));
  });

  it('routes NOTES practice exam to pdfExporter', () => {
    const payload: NotesPayload = { document_summary: '', flashcards: [], practice_exam: [] };
    exportStudyAssets(payload, { format: 'pdf', docType: 'NOTES' });
    expect(pdfExporter.exportToPdf).toHaveBeenCalledWith(payload, expect.any(Object));
  });

  it('routes SYLLABUS to pdfExporter', () => {
    const payload: SyllabusPayload = { course_title: 'X', total_units: 1, learning_path: [], priority_topics: [] };
    exportStudyAssets(payload, { format: 'pdf', docType: 'SYLLABUS' });
    expect(pdfExporter.exportToPdf).toHaveBeenCalledWith(payload, expect.any(Object));
  });

  it('routes PYQ to pdfExporter', () => {
    const payload: PYQAnalysisPayload = { topic_frequency: [], predicted_questions: [] };
    exportStudyAssets(payload, { format: 'pdf', docType: 'PYQ' });
    expect(pdfExporter.exportToPdf).toHaveBeenCalledWith(payload, expect.any(Object));
  });

  it('throws when CSV requested with SYLLABUS', () => {
    const payload: SyllabusPayload = { course_title: 'X', total_units: 1, learning_path: [], priority_topics: [] };
    expect(() => exportStudyAssets(payload, { format: 'csv', docType: 'SYLLABUS' }))
      .toThrow('CSV export is only available for NOTES and PYQ');
  });
});
