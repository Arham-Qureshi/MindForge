import express from "express";
import { healthRouter } from "./routes/health.routes.js";
import { documentRouter } from "./routes/document.routes.js";
import { jobRouter } from "./routes/job.routes.js";
import { corsMiddleware } from "./middleware/cors.middleware.js";
import { errorMiddleware } from "./middleware/error.middleware.js";

export function createApp() {
  const app = express();
  app.use(express.json());
  app.use(corsMiddleware);
  app.use("/api/health", healthRouter);
  app.use("/api/document", documentRouter);
  app.use("/api/jobs", jobRouter);
  app.use(errorMiddleware);
  return app;
}
