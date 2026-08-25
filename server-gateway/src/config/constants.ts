export const MAX_FILE_SIZE = 15 * 1024 * 1024;
export const RATE_LIMIT_WINDOW_MS = 5 * 60 * 1000;
export const RATE_LIMIT_MAX = 5;
// upload now returns 202 fast; heavy LLM work happens async inside the engine
export const PY_PROXY_TIMEOUT_MS = 30 * 1000;
export const PY_JOBS_TIMEOUT_MS = 5 * 1000;
export const UUID_V4_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export const ERR = {
  NO_FILE: "ERR_400_NO_FILE",
  BAD_MIME: "ERR_400_BAD_MIME",
  FILE_TOO_LARGE: "ERR_413_FILE_TOO_LARGE",
  RATE_LIMIT: "ERR_429_RATE_LIMIT",
  GATEWAY_DOWN: "ERR_503",
  BAD_JOB_ID: "ERR_400_BAD_JOB_ID",
} as const;
