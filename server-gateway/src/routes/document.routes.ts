import { Router } from "express";
import rateLimit from "express-rate-limit";
import { RATE_LIMIT_WINDOW_MS, RATE_LIMIT_MAX, ERR } from "../config/constants.js";

export const documentRouter = Router();

const uploadRateLimiter = rateLimit({
  windowMs: RATE_LIMIT_WINDOW_MS,
  max: RATE_LIMIT_MAX,
  standardHeaders: true,
  legacyHeaders: false,
  handler: (_req, res) =>
    res.status(429).json({
      error: ERR.RATE_LIMIT,
      message: "Too many requests! Please wait 5 minutes before uploading another file.",
    }),
});

documentRouter.use(uploadRateLimiter);
