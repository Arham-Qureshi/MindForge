import axios from "axios";
import FormData from "form-data";
import { env } from "../config/env.config.js";
import { PY_PROXY_TIMEOUT_MS, PY_JOBS_TIMEOUT_MS } from "../config/constants.js";

export class PythonEngineDownError extends Error {}
export class PythonEngineError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

type UpstreamResult = { status: number; data: unknown };

export type ProcessParams = {
  mode?: string;
  flashcardCount?: number;
};

function mapUpstreamError(err: unknown): never | undefined {
  if (axios.isAxiosError(err) && (err.code === "ECONNREFUSED" || err.code === "ECONNABORTED")) {
    throw new PythonEngineDownError("python engine unreachable");
  }
  if (axios.isAxiosError(err) && err.response) {
    const upstream = err.response;
    const detail = upstream.data?.detail;
    const message = typeof detail === "string" ? detail : detail?.message ?? upstream.statusText;
    const code = typeof detail === "string" ? "ERR_UPSTREAM" : detail?.error ?? "ERR_UPSTREAM";
    throw new PythonEngineError(upstream.status, code, message);
  }
  return undefined;
}

export async function forwardToPythonEngine(
  fileBuffer: Buffer,
  params?: ProcessParams,
): Promise<UpstreamResult> {
  const form = new FormData();
  form.append("file", fileBuffer, {
    filename: "document.pdf",
    contentType: "application/pdf",
  });

  const parts: string[] = [];
  if (params?.mode) parts.push(`mode=${params.mode}`);
  if (params?.flashcardCount) parts.push(`flashcard_count=${params.flashcardCount}`);
  const query = parts.length ? `?${parts.join("&")}` : "";

  try {
    const res = await axios.post(
      `${env.pythonEngineUrl}/api/v1/document/process${query}`,
      form,
      { timeout: PY_PROXY_TIMEOUT_MS, headers: form.getHeaders() },
    );
    return { status: res.status, data: res.data };
  } catch (err) {
    mapUpstreamError(err);
    throw err;
  }
}

export async function fetchJobStatus(jobId: string): Promise<UpstreamResult> {
  try {
    const res = await axios.get(`${env.pythonEngineUrl}/api/v1/jobs/${jobId}`, {
      timeout: PY_JOBS_TIMEOUT_MS,
    });
    return { status: res.status, data: res.data };
  } catch (err) {
    mapUpstreamError(err);
    throw err;
  }
}

export async function cancelJob(jobId: string): Promise<UpstreamResult> {
  try {
    const res = await axios.delete(`${env.pythonEngineUrl}/api/v1/jobs/${jobId}`, {
      timeout: PY_JOBS_TIMEOUT_MS,
    });
    return { status: res.status, data: res.data };
  } catch (err) {
    mapUpstreamError(err);
    throw err;
  }
}
