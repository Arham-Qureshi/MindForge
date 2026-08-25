import axios from "axios";
import FormData from "form-data";
import { env } from "../config/env.config.js";
import { PY_PROXY_TIMEOUT_MS } from "../config/constants.js";

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

export async function forwardToPythonEngine(fileBuffer: Buffer): Promise<unknown> {
  const form = new FormData();
  form.append("file", fileBuffer, {
    filename: "document.pdf",
    contentType: "application/pdf",
  });

  try {
    const res = await axios.post(`${env.pythonEngineUrl}/api/v1/document/process`, form, {
      timeout: PY_PROXY_TIMEOUT_MS,
      headers: form.getHeaders(),
    });
    return res.data;
  } catch (err) {
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
    throw err;
  }
}
