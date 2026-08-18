import { describe, it, expect, vi, beforeEach } from "vitest";
import axios from "axios";
import { forwardToPythonEngine, PythonEngineDownError } from "../src/services/pythonProxy.service.js";

describe("forwardToPythonEngine", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns engine response data on success", async () => {
    vi.spyOn(axios, "post").mockResolvedValue({ data: { docType: "NOTES" } });
    await expect(forwardToPythonEngine(Buffer.from("%PDF-1.7\ncontent"))).resolves.toEqual({
      docType: "NOTES",
    });
  });

  it("throws PythonEngineDownError on ECONNREFUSED", async () => {
    vi.spyOn(axios, "post").mockRejectedValue({ isAxiosError: true, code: "ECONNREFUSED" });
    await expect(forwardToPythonEngine(Buffer.from("x"))).rejects.toBeInstanceOf(
      PythonEngineDownError,
    );
  });

  it("throws PythonEngineDownError on timeout (ECONNABORTED)", async () => {
    vi.spyOn(axios, "post").mockRejectedValue({ isAxiosError: true, code: "ECONNABORTED" });
    await expect(forwardToPythonEngine(Buffer.from("x"))).rejects.toBeInstanceOf(
      PythonEngineDownError,
    );
  });

  it("rethrows other axios errors as-is", async () => {
    const err = { isAxiosError: true, code: "ERR_BAD_RESPONSE" };
    vi.spyOn(axios, "post").mockRejectedValue(err);
    await expect(forwardToPythonEngine(Buffer.from("x"))).rejects.toBe(err);
  });
});