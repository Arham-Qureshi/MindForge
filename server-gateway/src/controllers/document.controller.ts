import type { Request, Response } from "express";
import { forwardToPythonEngine, PythonEngineDownError } from "../services/pythonProxy.service.js";
import { ERR } from "../config/constants.js";

export async function processDocument(req: Request, res: Response) {
  try {
    const fileBuffer = req.file?.buffer;
    if (!fileBuffer) {
      return res.status(400).json({ error: ERR.NO_FILE, message: "No file provided." });
    }

    const result = await forwardToPythonEngine(fileBuffer);
    return res.status(200).json(result);
  } catch (err) {
    if (err instanceof PythonEngineDownError) {
      return res.status(503).json({ error: ERR.GATEWAY_DOWN, message: "AI Microservice offline" });
    }
    console.error(err);
    return res.status(500).json({ error: "ERR_500_INTERNAL", message: "Internal Gateway Error" });
  } finally {
    req.file = undefined;
  }
}
