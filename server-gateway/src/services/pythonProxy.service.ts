import axios from "axios";
import FormData from "form-data";
import { env } from "../config/env.config.js";
import { PY_PROXY_TIMEOUT_MS } from "../config/constants.js";

export class PythonEngineDownError extends Error {}

export async function forwardToPythonEngine(fileBuffer: Buffer): Promise<unknown> {
  const form = new FormData();
  form.append("file", fileBuffer, {
    filename: "document.pdf",
    contentType: "application/pdf",
  });

  try {
    const res = await axios.post(env.pythonEngineUrl, form, {
      timeout: PY_PROXY_TIMEOUT_MS,
      headers: form.getHeaders(),
    });
    return res.data;
  } catch (err) {
    if (axios.isAxiosError(err) && (err.code === "ECONNREFUSED" || err.code === "ECONNABORTED")) {
      throw new PythonEngineDownError("python engine unreachable");
    }
    throw err;
  }
}
