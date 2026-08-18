import "dotenv/config";

export const env = {
  port: Number(process.env.PORT ?? 5000),
  pythonEngineUrl: process.env.PYTHON_ENGINE_URL ?? "http://localhost:8000",
  corsOrigin: process.env.CORS_ORIGIN ?? "http://localhost:5173",
};
