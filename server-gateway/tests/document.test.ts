import { describe, it, expect, vi, beforeEach } from "vitest";
import request from "supertest";
import express from "express";
import type { Request } from "express";
import { uploadMiddleware, validatePDFHeader } from "../src/middleware/upload.middleware.js";
import { errorMiddleware } from "../src/middleware/error.middleware.js";
import { processDocument } from "../src/controllers/document.controller.js";
import * as proxyService from "../src/services/pythonProxy.service.js";

let serverReq: Request | undefined;

function makeApp() {
  const app = express();
  app.use((req, _res, next) => {
    serverReq = req;
    next();
  });
  app.post("/process", uploadMiddleware, validatePDFHeader, processDocument);
  app.use(errorMiddleware);
  return app;
}

describe("POST /process", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    serverReq = undefined;
  });

  it("forwards buffer and passes through engine 202 + body, clearing req.file", async () => {
    vi.spyOn(proxyService, "forwardToPythonEngine").mockResolvedValue({
      status: 202,
      data: { job_id: "abc-123", chunks_total: 4 },
    });
    const app = makeApp();
    const res = await request(app)
      .post("/process")
      .attach("file", Buffer.from("%PDF-1.7\ncontent"), "doc.pdf");
    expect(res.status).toBe(202);
    expect(res.body).toEqual({ job_id: "abc-123", chunks_total: 4 });
    expect(proxyService.forwardToPythonEngine).toHaveBeenCalledOnce();
    expect(serverReq?.file).toBeUndefined();
  });

  it("returns 503 ERR_503 when the python engine is down", async () => {
    const err = new proxyService.PythonEngineDownError("ECONNREFUSED");
    vi.spyOn(proxyService, "forwardToPythonEngine").mockRejectedValue(err);
    const app = makeApp();
    const res = await request(app)
      .post("/process")
      .attach("file", Buffer.from("%PDF-1.7\ncontent"), "doc.pdf");
    expect(res.status).toBe(503);
    expect(res.body.error).toBe("ERR_503");
  });

  it("propagates upstream HTTP errors from the python engine", async () => {
    const err = new proxyService.PythonEngineError(400, "ERR_400", "PDF is encrypted");
    vi.spyOn(proxyService, "forwardToPythonEngine").mockRejectedValue(err);
    const app = makeApp();
    const res = await request(app)
      .post("/process")
      .attach("file", Buffer.from("%PDF-1.7\ncontent"), "doc.pdf");
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("ERR_400");
    expect(res.body.message).toBe("PDF is encrypted");
  });

  it("forwards mode and flashcard_count query params to the engine", async () => {
    vi.spyOn(proxyService, "forwardToPythonEngine").mockResolvedValue({
      status: 202,
      data: { job_id: "test-123", chunks_total: 1 },
    });
    const app = makeApp();
    await request(app)
      .post("/process?mode=notes&flashcard_count=15")
      .attach("file", Buffer.from("%PDF-1.7\ncontent"), "doc.pdf");
    expect(proxyService.forwardToPythonEngine).toHaveBeenCalledWith(
      expect.any(Buffer),
      { mode: "notes", flashcardCount: 15 },
    );
  });
});