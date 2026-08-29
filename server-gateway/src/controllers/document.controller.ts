import type { Request, Response } from "express";
import {
  forwardToPythonEngine,
  forwardReprocessToPythonEngine,
  PythonEngineDownError,
  PythonEngineError,
} from "../services/pythonProxy.service.js";
import { ERR } from "../config/constants.js";

export async function processDocument(req: Request, res: Response) {
  try {
    const fileBuffer = req.file?.buffer;
    if (!fileBuffer) {
      return res.status(400).json({ error: ERR.NO_FILE, message: "No file provided." });
    }

    const mode = req.query.mode as string | undefined;
    const flashcardCount = req.query.flashcard_count
      ? Number(req.query.flashcard_count)
      : undefined;
    const notesSubtask = req.query.notes_subtask as string | undefined;

    const { status, data } = await forwardToPythonEngine(fileBuffer, {
      mode,
      flashcardCount,
      notesSubtask,
    });
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
  } finally {
    req.file = undefined;
  }
}

export async function reprocessDocument(req: Request, res: Response) {
  try {
    const mode = req.query.mode as string | undefined;
    const flashcardCount = req.query.flashcard_count
      ? Number(req.query.flashcard_count)
      : undefined;
    const notesSubtask = req.query.notes_subtask as string | undefined;
    const chunks = (req.body as { chunks?: unknown })?.chunks;

    if (!Array.isArray(chunks)) {
      return res.status(400).json({ error: ERR.NO_FILE, message: "Missing chunks array." });
    }

    const { status, data } = await forwardReprocessToPythonEngine(chunks as string[], {
      mode,
      flashcardCount,
      notesSubtask,
    });
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
