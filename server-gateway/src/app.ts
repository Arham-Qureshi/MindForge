import express from "express";
import { healthRouter } from "./routes/health.routes.js";
import { errorMiddleware } from "./middleware/error.middleware.js";

export function createApp() {
  const app = express();
  app.use(express.json());
  app.use("/api/health", healthRouter);
  app.use(errorMiddleware);
  return app;
}
