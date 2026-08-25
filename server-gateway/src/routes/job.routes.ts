import { Router } from "express";
import { getJob, deleteJob } from "../controllers/job.controller.js";

// polling endpoint: intentionally NOT behind the upload rate limiter
export const jobRouter = Router();

jobRouter.get("/:id", getJob);
jobRouter.delete("/:id", deleteJob);
