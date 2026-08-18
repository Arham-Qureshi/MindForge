import express from "express";
import { healthRouter } from "./routes/health.routes.js";

export function createApp() {
  const app = express();
  app.use(express.json());
  app.use("/api/health", healthRouter);
  return app;
}
