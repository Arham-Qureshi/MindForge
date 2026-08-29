import multer from "multer";
import type { Request, Response, NextFunction } from "express";
import { MAX_FILE_SIZE, ERR } from "../config/constants.js";

const storage = multer.memoryStorage();

export const uploadMiddleware = multer({
  storage,
  limits: { fileSize: MAX_FILE_SIZE },
}).fields([
  { name: "file", maxCount: 1 },
  { name: "files", maxCount: 10 },
]);

function getFiles(req: Request): Express.Multer.File[] {
  const single = (req as unknown as { file?: Express.Multer.File }).file;
  if (single) return [single];
  const multi = (req as unknown as { files?: Record<string, Express.Multer.File[]> }).files;
  if (multi) {
    if (Array.isArray(multi)) return multi as unknown as Express.Multer.File[];
    return [...(multi["file"] ?? []), ...(multi["files"] ?? [])];
  }
  return [];
}

export function validatePDFHeader(req: Request, res: Response, next: NextFunction) {
  const files = getFiles(req);
  if (files.length === 0) {
    return res.status(400).json({ error: ERR.NO_FILE, message: "Please drag and drop a valid PDF document to start." });
  }

  for (const file of files) {
    const header = file.buffer.subarray(0, 4).toString("utf8");
    if (header !== "%PDF") {
      return res.status(400).json({
        error: ERR.BAD_MIME,
        message: "Invalid file format. Please upload an authentic PDF document.",
      });
    }
  }

  next();
}