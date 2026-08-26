import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { documentService, DocumentUploadError } from './documentService';

const API_URL = 'http://localhost:5000';

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn());
});

afterEach(() => vi.restoreAllMocks());

describe('documentService.processDocument', () => {
  it('sends POST with mode query param', async () => {
    const accepted = { job_id: 'j1', chunks_total: 3 };
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 202,
      json: () => Promise.resolve(accepted),
    } as Response);

    const file = new File(['pdf'], 'doc.pdf', { type: 'application/pdf' });
    const result = await documentService.processDocument(file, 'notes');

    expect(result).toEqual(accepted);
    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string;
    expect(calledUrl).toContain(`${API_URL}/api/document/process?mode=notes`);
  });

  it('appends flashcard_count for notes mode', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 202,
      json: () => Promise.resolve({ job_id: 'j2', chunks_total: 5 }),
    } as Response);

    const file = new File(['pdf'], 'doc.pdf', { type: 'application/pdf' });
    await documentService.processDocument(file, 'notes', 10);

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string;
    expect(calledUrl).toContain('mode=notes');
    expect(calledUrl).toContain('flashcard_count=10');
  });

  it('omits flashcard_count when not notes mode', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 202,
      json: () => Promise.resolve({ job_id: 'j3', chunks_total: 2 }),
    } as Response);

    const file = new File(['pdf'], 'doc.pdf', { type: 'application/pdf' });
    await documentService.processDocument(file, 'pyq', 10);

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string;
    expect(calledUrl).toContain('mode=pyq');
    expect(calledUrl).not.toContain('flashcard_count');
  });

  it('throws DocumentUploadError on HTTP error', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 413,
      json: () => Promise.resolve({ error: 'ERR_413_FILE_TOO_LARGE' }),
    } as Response);

    const file = new File(['big'], 'big.pdf', { type: 'application/pdf' });
    await expect(documentService.processDocument(file, 'syllabus'))
      .rejects.toThrow(DocumentUploadError);
  });
});

describe('documentService.getJob', () => {
  it('fetches job status by id', async () => {
    const status = { status: 'done', doc_type: 'NOTES', chunks_done: 3, chunks_total: 3 };
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(status),
    } as Response);

    const result = await documentService.getJob('j1');
    expect(result).toEqual(status);
    expect(fetch).toHaveBeenCalledWith(`${API_URL}/api/jobs/j1`);
  });
});

describe('documentService.cancelJob', () => {
  it('sends DELETE for job id', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ status: 'cancelled' }),
    } as Response);

    await documentService.cancelJob('j1');
    expect(fetch).toHaveBeenCalledWith(`${API_URL}/api/jobs/j1`, { method: 'DELETE' });
  });
});
