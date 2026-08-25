import { describe, it, expect, vi, beforeEach } from "vitest";
import request from "supertest";
import express from "express";
import axios from "axios";
import * as proxyService from "../src/services/pythonProxy.service.js";
import { getJob, deleteJob } from "../src/controllers/job.controller.js";
import { errorMiddleware } from "../src/middleware/error.middleware.js";

function makeApp() {
  const app = express();
  app.use(express.json());
  app.get("/api/jobs/:id", getJob);
  app.delete("/api/jobs/:id", deleteJob);
  app.use(errorMiddleware);
  return app;
}

const UUID = "3fa85f64-5717-4562-b3fc-2c963f66afa6";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("GET /api/jobs/:id", () => {
  it("rejects malformed job ids locally with 422", async () => {
    const spy = vi.spyOn(axios, "get");
    const res = await request(makeApp()).get("/api/jobs/not-a-uuid");
    expect(res.status).toBe(422);
    expect(res.body.error).toBe("ERR_400_BAD_JOB_ID");
    expect(spy).not.toHaveBeenCalled();
  });

  it("passes through engine status and body", async () => {
    vi.spyOn(proxyService, "fetchJobStatus").mockResolvedValue({
      status: 200,
      data: { status: "processing", chunks_done: 1, chunks_total: 3 },
    });
    const res = await request(makeApp()).get(`/api/jobs/${UUID}`);
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("processing");
    expect(res.body.chunks_done).toBe(1);
  });

  it("passes through upstream 404 for unknown jobs", async () => {
    const err = Object.assign(new Error("nope"), {
      isAxiosError: true,
      response: {
        status: 404,
        statusText: "Not Found",
        data: { detail: { message: "Job not found." } },
      },
    });
    vi.spyOn(axios, "get").mockRejectedValue(err);
    const res = await request(makeApp()).get(`/api/jobs/${UUID}`);
    expect(res.status).toBe(404);
    expect(res.body.message).toBe("Job not found.");
  });

  it("returns 503 when the engine is down", async () => {
    vi.spyOn(proxyService, "fetchJobStatus").mockRejectedValue(
      new proxyService.PythonEngineDownError("down"),
    );
    const res = await request(makeApp()).get(`/api/jobs/${UUID}`);
    expect(res.status).toBe(503);
    expect(res.body.error).toBe("ERR_503");
  });
});

describe("DELETE /api/jobs/:id", () => {
  it("rejects malformed job ids locally with 422", async () => {
    const spy = vi.spyOn(axios, "delete");
    const res = await request(makeApp()).delete("/api/jobs/not-a-uuid");
    expect(res.status).toBe(422);
    expect(res.body.error).toBe("ERR_400_BAD_JOB_ID");
    expect(spy).not.toHaveBeenCalled();
  });

  it("passes through engine cancellation response", async () => {
    vi.spyOn(axios, "delete").mockResolvedValue({
      status: 200,
      data: { status: "cancelled" },
    });
    const res = await request(makeApp()).delete(`/api/jobs/${UUID}`);
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("cancelled");
  });

  it("returns 503 when the engine is down", async () => {
    vi.spyOn(proxyService, "cancelJob").mockRejectedValue(
      new proxyService.PythonEngineDownError("down"),
    );
    const res = await request(makeApp()).delete(`/api/jobs/${UUID}`);
    expect(res.status).toBe(503);
    expect(res.body.error).toBe("ERR_503");
  });
});
