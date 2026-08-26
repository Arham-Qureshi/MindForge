import { describe, it, expect, vi, beforeEach } from 'vitest';
import { exportToPdf } from './pdfExporter';
import type { NotesPayload, SyllabusPayload, PYQAnalysisPayload } from '../types/api.types';

const mockText = vi.fn();
const mockSave = vi.fn();
const mockAddPage = vi.fn();
const mockSetFontSize = vi.fn();
const mockSetFont = vi.fn();

vi.mock('jspdf', () => {
  return {
    default: vi.fn().mockImplementation(function () {
      return {
        text: mockText,
        save: mockSave,
        addPage: mockAddPage,
        setFontSize: mockSetFontSize,
        setFont: mockSetFont,
        internal: { pageSize: { getWidth: () => 210, getHeight: () => 297 } },
      };
    }),
  };
});

describe('exportToPdf', () => {
  beforeEach(() => vi.clearAllMocks());

  describe('NOTES (practice exam)', () => {
    const payload: NotesPayload = {
      document_summary: 'Test summary',
      flashcards: [],
      practice_exam: [
        {
          question: 'What is 2+2?',
          options: ['3', '4', '5', '6'] as [string, string, string, string],
          correct_answer_index: 1,
          solution: 'Basic arithmetic',
        },
      ],
    };

    it('generates PDF with questions and answer key', () => {
      exportToPdf(payload, { format: 'pdf', docType: 'NOTES' });
      expect(mockText).toHaveBeenCalled();
      expect(mockSave).toHaveBeenCalledWith('mindforge-notes-export.pdf');
    });

    it('creates a new page for answer key', () => {
      exportToPdf(payload, { format: 'pdf', docType: 'NOTES' });
      expect(mockAddPage).toHaveBeenCalled();
    });
  });

  describe('SYLLABUS', () => {
    const payload: SyllabusPayload = {
      course_title: 'Data Structures',
      total_units: 2,
      learning_path: [
        { unit_number: 1, title: 'Arrays', estimated_hours: 10, topics: ['Linear Search', 'Binary Search'], cognitive_level: 'Understand' },
      ],
      priority_topics: [{ topic: 'Binary Search', weightage: 35 }],
    };

    it('generates PDF with course title and units', () => {
      exportToPdf(payload, { format: 'pdf', docType: 'SYLLABUS' });
      expect(mockText).toHaveBeenCalled();
      expect(mockSave).toHaveBeenCalledWith('mindforge-syllabus-export.pdf');
    });
  });

  describe('PYQ', () => {
    const payload: PYQAnalysisPayload = {
      topic_frequency: [{ topic: 'Arrays', percentage: 40, question_count: 5 }],
      predicted_questions: [
        { question: 'Explain binary search', bloom_level: 'Analyze', expected_marks: 10, probability_score: 0.85 },
      ],
    };

    it('generates PDF with topic frequency and predictions', () => {
      exportToPdf(payload, { format: 'pdf', docType: 'PYQ' });
      expect(mockText).toHaveBeenCalled();
      expect(mockSave).toHaveBeenCalledWith('mindforge-pyq-export.pdf');
    });
  });

  it('uses custom filename when provided', () => {
    const payload: NotesPayload = { document_summary: '', flashcards: [], practice_exam: [] };
    exportToPdf(payload, { format: 'pdf', docType: 'NOTES', filename: 'custom.pdf' });
    expect(mockSave).toHaveBeenCalledWith('custom.pdf');
  });
});
