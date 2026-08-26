import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { exportToJson } from './jsonExporter';
import type { SyllabusPayload } from '../types/api.types';

describe('exportToJson', () => {
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

  it('exports syllabus payload as valid JSON', async () => {
    const payload: SyllabusPayload = {
      course_title: 'Test Course',
      total_units: 2,
      learning_path: [],
      priority_topics: [],
    };
    exportToJson(payload, { format: 'json', docType: 'SYLLABUS' });
    expect(createdBlob).toBeTruthy();
    const text = await createdBlob!.text();
    const parsed = JSON.parse(text);
    expect(parsed.course_title).toBe('Test Course');
  });

  it('uses custom filename when provided', () => {
    const payload = { course_title: 'X', total_units: 1, learning_path: [], priority_topics: [] };
    const spy = document.createElement as any;
    exportToJson(payload, { format: 'json', docType: 'SYLLABUS', filename: 'custom.json' });
    expect(spy.mock.results[0].value.download).toBe('custom.json');
  });
});
