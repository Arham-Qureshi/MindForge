import cors from "cors";
import { env } from "../config/env.config.js";

export const corsMiddleware = cors({
  origin: (origin, callback) => {
    const allowed = !origin || origin === env.corsOrigin;
    callback(allowed ? null : new Error("Not allowed by CORS"), allowed);
  },
});
