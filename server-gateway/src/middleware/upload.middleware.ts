import multer from "multer";
import type { Request, Response, NextFunction } from "express";
import { MAX_FILE_SIZE, ERR } from "../config/constants.js";

const storage = multer.memoryStorage();

export const uploadMiddleware = multer({
  storage,
  limits: { fileSize: MAX_FILE_SIZE },
}).single("file");

export function validatePDFHeader(req: Request, res: Response, next: NextFunction) {
  const file = req.file;
  if (!file) {
    return res.status(400).json({ error: ERR.NO_FILE, message: "Please drag and drop a valid PDF document to start." });
  }

  const header = file.buffer.subarray(0, 4).toString("utf8");
  if (header !== "%PDF") {
    return res.status(400).json({
      error: ERR.BAD_MIME,
      message: "Invalid file format. Please upload an authentic PDF document.",
    });
  }

  next();
}