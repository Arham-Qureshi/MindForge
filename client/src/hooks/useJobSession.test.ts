import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useJobSession } from "./useJobSession";

const JOB = { job_id: "11111111-2222-4333-8444-555555555555", chunks_total: 3 };

function fetchRespondingWith(responses: Array<{ body: unknown; ok?: boolean; status?: number }>) {
  let call = 0;
  return vi.fn().mockImplementation(() => {
    const res = responses[Math.min(call++, responses.length - 1)];
    return Promise.resolve({
      ok: res.ok ?? true,
      status: res.status ?? 200,
      json: () => Promise.resolve(res.body),
    });
  });
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("useJobSession", () => {
  it("starts idle", () => {
    const { result } = renderHook(() => useJobSession());
    expect(result.current.phase.kind).toBe("idle");
  });

  it("persists the job and polls until done", async () => {
    vi.useFakeTimers();
    const fetchMock = fetchRespondingWith([
      { body: { status: "processing", doc_type: "NOTES", chunks_done: 0, chunks_total: 3 } },
      { body: { status: "processing", doc_type: "NOTES", chunks_done: 2, chunks_total: 3 } },
      {
        body: {
          status: "done",
          doc_type: "NOTES",
          chunks_done: 3,
          chunks_total: 3,
          classification: { doc_type: "NOTES", confidence: 0.9, metrics: {} },
          payload: { document_summary: "s", flashcards: [], practice_exam: [] },
        },
      },
    ]);
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useJobSession());

    act(() => result.current.startJob(JOB));
    expect(result.current.phase.kind).toBe("processing");
    expect(JSON.parse(localStorage.getItem("mf.active_job")!)).toEqual(JOB);

    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    const afterFirstPoll = result.current.phase;
    expect(afterFirstPoll.kind).toBe("processing");

    await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
    const afterSecondPoll = result.current.phase;
    if (afterSecondPoll.kind === "processing") {
      expect(afterSecondPoll.chunksDone).toBe(2);
    } else {
      expect.unreachable("expected processing after second poll");
    }

    await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
    const afterThirdPoll = result.current.phase;
    expect(afterThirdPoll.kind).toBe("ready");
    if (afterThirdPoll.kind === "ready") {
      expect(afterThirdPoll.data.payload).toEqual({
        document_summary: "s",
        flashcards: [],
        practice_exam: [],
      });
    }
    expect(localStorage.getItem("mf.active_job")).toBeNull();
  });

  it("surfaces the job error on failure", async () => {
    vi.useFakeTimers();
    const fetchMock = fetchRespondingWith([
      {
        body: {
          status: "failed",
          doc_type: "NOTES",
          chunks_done: 0,
          chunks_total: 2,
          error: "AI provider error (400): bad key",
        },
      },
    ]);
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useJobSession());
    act(() => result.current.startJob(JOB));

    await act(async () => { await vi.advanceTimersByTimeAsync(0); });

    expect(result.current.phase.kind).toBe("failed");
    if (result.current.phase.kind === "failed") {
      expect(result.current.phase.message).toContain("bad key");
    }
    expect(localStorage.getItem("mf.active_job")).toBeNull();
  });

  it("resumes an active job from localStorage after refresh", async () => {
    vi.useFakeTimers();
    localStorage.setItem("mf.active_job", JSON.stringify(JOB));
    const fetchMock = fetchRespondingWith([
      { body: { status: "processing", doc_type: "NOTES", chunks_done: 1, chunks_total: 3 } },
    ]);
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useJobSession());
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });

    expect(result.current.phase.kind).toBe("processing");
    expect(fetchMock).toHaveBeenCalled();
  });

  it("fails the session after repeated poll errors instead of spinning forever", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn().mockRejectedValue(new Error("network gone"));
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useJobSession());
    act(() => result.current.startJob(JOB));

    // ~10 failed polls at 2s each
    await act(async () => { await vi.advanceTimersByTimeAsync(20_000); });

    expect(result.current.phase.kind).toBe("failed");
    if (result.current.phase.kind === "failed") {
      expect(result.current.phase.message).toContain("connection");
    }
    expect(localStorage.getItem("mf.active_job")).toBeNull();
  });

  it("reset clears everything", async () => {
    vi.useFakeTimers();
    const fetchMock = fetchRespondingWith([
      { body: { status: "processing", doc_type: "NOTES", chunks_done: 0, chunks_total: 3 } },
    ]);
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useJobSession());
    act(() => result.current.startJob(JOB));
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });

    act(() => result.current.reset());
    expect(result.current.phase.kind).toBe("idle");
    expect(localStorage.getItem("mf.active_job")).toBeNull();

    await act(async () => { await vi.advanceTimersByTimeAsync(6000); });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});

describe("useJobSession kill", () => {
  it("clears the session immediately and cancels server-side", async () => {
    vi.useFakeTimers();
    const calls: Array<{ method: string; url: string }> = [];
    const fetchMock = vi.fn().mockImplementation((_url: string, init?: { method?: string }) => {
      calls.push({ method: init?.method ?? "GET", url: String(_url) });
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve(
            init?.method === "DELETE"
              ? { status: "cancelled" }
              : { status: "processing", doc_type: "NOTES", chunks_done: 1, chunks_total: 3 },
          ),
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useJobSession());
    act(() => result.current.startJob(JOB));
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    expect(result.current.phase.kind).toBe("processing");

    await act(async () => { await result.current.kill(); });

    expect(result.current.phase.kind).toBe("idle");
    expect(localStorage.getItem("mf.active_job")).toBeNull();

    await act(async () => { await vi.advanceTimersByTimeAsync(6000); });
    const polls = calls.filter((c) => c.method === "GET");
    const deletes = calls.filter((c) => c.method === "DELETE");
    expect(deletes).toHaveLength(1);
    expect(deletes[0].url).toContain(JOB.job_id);
    expect(polls.length).toBeLessThan(3);
  });

  it("still resets locally when the engine rejects the cancel", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("engine down")));

    const { result } = renderHook(() => useJobSession());
    act(() => result.current.startJob(JOB));

    await act(async () => { await result.current.kill(); });

    expect(result.current.phase.kind).toBe("idle");
    expect(localStorage.getItem("mf.active_job")).toBeNull();
  });
});
