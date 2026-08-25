import type { Request, Response } from "express";
import {
  fetchJobStatus,
  cancelJob,
  PythonEngineDownError,
  PythonEngineError,
} from "../services/pythonProxy.service.js";
import { ERR, UUID_V4_RE } from "../config/constants.js";

export async function getJob(req: Request, res: Response) {
  const { id } = req.params;
  if (!UUID_V4_RE.test(id)) {
    return res.status(422).json({ error: ERR.BAD_JOB_ID, message: "Invalid job id." });
  }

  try {
    const { status, data } = await fetchJobStatus(id);
    return res.status(status).json(data);
  } catch (err) {
    if (err instanceof PythonEngineDownError) {
      return res.status(503).json({ error: ERR.GATEWAY_DOWN, message: "AI Microservice offline" });
    }
    if (err instanceof PythonEngineError) {
      return res.status(err.status).json({ error: err.code, message: err.message });
    }
    console.error(err);
    return res.status(500).json({ error: "ERR_500_INTERNAL", message: "Internal Gateway Error" });
  }
}

export async function deleteJob(req: Request, res: Response) {
  const { id } = req.params;
  if (!UUID_V4_RE.test(id)) {
    return res.status(422).json({ error: ERR.BAD_JOB_ID, message: "Invalid job id." });
  }

  try {
    const { status, data } = await cancelJob(id);
    return res.status(status).json(data);
  } catch (err) {
    if (err instanceof PythonEngineDownError) {
      return res.status(503).json({ error: ERR.GATEWAY_DOWN, message: "AI Microservice offline" });
    }
    if (err instanceof PythonEngineError) {
      return res.status(err.status).json({ error: err.code, message: err.message });
    }
    console.error(err);
    return res.status(500).json({ error: "ERR_500_INTERNAL", message: "Internal Gateway Error" });
  }
}
