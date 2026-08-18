import type { Request, Response, NextFunction } from "express";
import multer from "multer";
import { ERR } from "../config/constants.js";

export function errorMiddleware(err: unknown, _req: Request, res: Response, _next: NextFunction) {
  if (err instanceof multer.MulterError && err.code === "LIMIT_FILE_SIZE") {
    return res.status(413).json({
      error: ERR.FILE_TOO_LARGE,
      message: "File is too large. Maximum supported document size is 15 MB.",
    });
  }

  console.error(err);
  return res.status(500).json({ error: "ERR_500_INTERNAL", message: "Internal Gateway Error" });
}