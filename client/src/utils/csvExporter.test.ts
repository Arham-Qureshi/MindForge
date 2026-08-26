import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { exportToCsv } from './csvExporter';
import type { NotesPayload, PYQAnalysisPayload } from '../types/api.types';

describe('exportToCsv', () => {
  let createdBlob: Blob | null = null;

  beforeEach(() => {
    vi.spyOn(URL, 'createObjectURL').mockImplementation((blob) => {
      createdBlob = blob as Blob;
      return 'blob:mock';
    });
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
    vi.spyOn(document, 'createElement').mockImplementation(() => {
      return { click: vi.fn(), href: '', download: '' } as any;
    });
  });

  afterEach(() => vi.restoreAllMocks());

  describe('NOTES (flashcards)', () => {
    const samplePayload: NotesPayload = {
      document_summary: 'Test summary',
      flashcards: [
        { front: 'What is X?', back: 'X is Y', bloom_category: 'Remember', difficulty: 'Easy' },
        { front: 'Compare A and B', back: 'A does this, B does that', bloom_category: 'Analyze', difficulty: 'Hard' },
      ],
      practice_exam: [],
    };

    it('produces Anki-compatible CSV with header + rows', async () => {
      exportToCsv(samplePayload, { format: 'csv', docType: 'NOTES' });
      expect(createdBlob).toBeTruthy();
      const text = await createdBlob!.text();
      const lines = text.trim().split('\n');
      expect(lines[0]).toBe('"Front","Back","Category"');
      expect(lines.length).toBe(3);
    });

    it('escapes commas in flashcard content', async () => {
      const payload: NotesPayload = {
        document_summary: '',
        flashcards: [
          { front: 'List A, B, C', back: 'Answer', bloom_category: 'Remember', difficulty: 'Easy' },
        ],
        practice_exam: [],
      };
      exportToCsv(payload, { format: 'csv', docType: 'NOTES' });
      const text = await createdBlob!.text();
      expect(text).toContain('"List A, B, C"');
    });
  });

  describe('PYQ (topic frequency)', () => {
    const pyqPayload: PYQAnalysisPayload = {
      topic_frequency: [
        { topic: 'Data Structures', percentage: 35.5, question_count: 12 },
        { topic: 'Algorithms', percentage: 28.3, question_count: 9 },
      ],
      predicted_questions: [],
    };

    it('produces CSV with Topic,Percentage,QuestionCount header', async () => {
      exportToCsv(pyqPayload, { format: 'csv', docType: 'PYQ' });
      expect(createdBlob).toBeTruthy();
      const text = await createdBlob!.text();
      const lines = text.trim().split('\n');
      expect(lines[0]).toBe('"Topic","Percentage","Question Count"');
      expect(lines.length).toBe(3);
    });

    it('uses default PYQ filename', () => {
      exportToCsv(pyqPayload, { format: 'csv', docType: 'PYQ' });
      const spy = document.createElement as any;
      expect(spy.mock.results[0].value.download).toMatch(/^mindforge-pyq-topics-\d+\.csv$/);
    });
  });
});
