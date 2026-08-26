import json
import sqlite3
import threading
import time

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'queued',
    task TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    chunks_total INTEGER NOT NULL,
    chunks_done INTEGER NOT NULL DEFAULT 0,
    user_mode TEXT NOT NULL DEFAULT '',
    flashcard_count INTEGER NOT NULL DEFAULT 10,
    payload TEXT,
    error TEXT,
    classification TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS job_chunks (
    job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    result TEXT,
    PRIMARY KEY (job_id, idx)
);
CREATE TABLE IF NOT EXISTS usage (
    provider TEXT PRIMARY KEY,
    win_start REAL NOT NULL DEFAULT 0,
    reqs INTEGER NOT NULL DEFAULT 0,
    tokens INTEGER NOT NULL DEFAULT 0,
    day_start REAL NOT NULL DEFAULT 0,
    day_reqs INTEGER NOT NULL DEFAULT 0,
    day_tokens INTEGER NOT NULL DEFAULT 0,
    penalty_until REAL NOT NULL DEFAULT 0
);
"""


def _empty_snapshot():
    return {
        "win_start": 0.0,
        "reqs": 0,
        "tokens": 0,
        "day_start": 0.0,
        "day_reqs": 0,
        "day_tokens": 0,
    }


class Store:
    MAX_ATTEMPTS = 5

    def __init__(self, db_path: str):
        self._lock = threading.RLock()
        self._db_path = db_path
        with self._conn() as conn:
            conn.executescript(_SCHEMA)
            try:
                conn.execute("ALTER TABLE jobs ADD COLUMN classification TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE jobs ADD COLUMN user_mode TEXT NOT NULL DEFAULT ''")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE jobs ADD COLUMN flashcard_count INTEGER NOT NULL DEFAULT 10")
            except sqlite3.OperationalError:
                pass

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=30)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def create_job(self, job_id: str, task: str, doc_type: str, chunks: list[str],
                   classification: dict | None = None, created_at: float | None = None,
                   user_mode: str = "", flashcard_count: int = 10):
        with self._lock, self._conn() as conn:
            conn.execute(
                "INSERT INTO jobs (id, task, doc_type, chunks_total, classification, created_at,"
                " user_mode, flashcard_count)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job_id,
                    task,
                    doc_type,
                    len(chunks),
                    json.dumps(classification) if classification else None,
                    created_at or time.time(),
                    user_mode or doc_type,
                    flashcard_count,
                ),
            )
            conn.executemany(
                "INSERT INTO job_chunks (job_id, idx, text) VALUES (?, ?, ?)",
                [(job_id, i, c) for i, c in enumerate(chunks)],
            )

    def get_job(self, job_id: str) -> dict | None:
        with self._lock, self._conn() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            return dict(row) if row else None

    def mark_processing(self, job_id: str):
        with self._lock, self._conn() as conn:
            conn.execute(
                "UPDATE jobs SET status = 'processing' WHERE id = ? AND status = 'queued'",
                (job_id,),
            )

    def pending_chunks(self, job_id: str) -> list[dict]:
        with self._lock, self._conn() as conn:
            rows = conn.execute(
                "SELECT idx, text, attempts FROM job_chunks "
                "WHERE job_id = ? AND status = 'pending' AND attempts < ? ORDER BY idx",
                (job_id, self.MAX_ATTEMPTS),
            ).fetchall()
            return [dict(r) for r in rows]

    def dead_chunks_count(self, job_id: str) -> int:
        with self._lock, self._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM job_chunks WHERE job_id = ? AND status = 'dead'",
                (job_id,),
            ).fetchone()
            return row["n"]

    def complete_chunk(self, job_id: str, idx: int, result_json: str):
        with self._lock, self._conn() as conn:
            conn.execute(
                "UPDATE job_chunks SET status = 'done', result = ? WHERE job_id = ? AND idx = ?",
                (result_json, job_id, idx),
            )
            conn.execute("UPDATE jobs SET chunks_done = chunks_done + 1 WHERE id = ?", (job_id,))

    def fail_chunk_attempt(self, job_id: str, idx: int):
        with self._lock, self._conn() as conn:
            conn.execute(
                "UPDATE job_chunks SET attempts = attempts + 1,"
                " status = CASE WHEN attempts + 1 >= ? THEN 'dead' ELSE status END"
                " WHERE job_id = ? AND idx = ?",
                (self.MAX_ATTEMPTS, job_id, idx),
            )

    def set_job_payload(self, job_id: str, payload_json: str):
        with self._lock, self._conn() as conn:
            conn.execute(
                # cancelled jobs must stay cancelled even if a straggler result lands
                "UPDATE jobs SET payload = ?, status = 'done'"
                " WHERE id = ? AND status != 'cancelled'",
                (payload_json, job_id),
            )

    def fail_job(self, job_id: str, error: str):
        with self._lock, self._conn() as conn:
            conn.execute(
                "UPDATE jobs SET error = ?, status = 'failed'"
                " WHERE id = ? AND status NOT IN ('cancelled', 'done')",
                (error, job_id),
            )

    def cancel_job(self, job_id: str) -> bool:
        with self._lock, self._conn() as conn:
            cur = conn.execute(
                "UPDATE jobs SET status = 'cancelled', error = 'Cancelled by user.'"
                " WHERE id = ? AND status IN ('queued', 'processing')",
                (job_id,),
            )
            return cur.rowcount > 0

    def purge_expired(self, ttl_hours: float, now: float | None = None):
        cutoff = (now or time.time()) - ttl_hours * 3600
        with self._lock, self._conn() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("DELETE FROM jobs WHERE created_at < ?", (cutoff,))

    def chunk_results(self, job_id: str) -> list[dict]:
        with self._lock, self._conn() as conn:
            rows = conn.execute(
                "SELECT result FROM job_chunks WHERE job_id = ? AND status = 'done' ORDER BY idx",
                (job_id,),
            ).fetchall()
            return [json.loads(r["result"]) for r in rows if r["result"]]

    # ---- rate limiter counters ----

    def snapshot(self, provider: str) -> dict:
        with self._lock, self._conn() as conn:
            row = conn.execute("SELECT * FROM usage WHERE provider = ?", (provider,)).fetchone()
            snap = _empty_snapshot()
            if row:
                snap.update({k: row[k] for k in snap})
            return snap

    def save_snapshot(self, provider: str, snap: dict):
        with self._lock, self._conn() as conn:
            conn.execute(
                "INSERT INTO usage (provider, win_start, reqs, tokens, day_start, day_reqs, day_tokens, penalty_until)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT penalty_until FROM usage WHERE provider = ?), 0))"
                " ON CONFLICT(provider) DO UPDATE SET win_start=?, reqs=?, tokens=?, day_start=?, day_reqs=?, day_tokens=?",
                (
                    provider,
                    snap["win_start"], snap["reqs"], snap["tokens"],
                    snap["day_start"], snap["day_reqs"], snap["day_tokens"],
                    provider,
                    snap["win_start"], snap["reqs"], snap["tokens"],
                    snap["day_start"], snap["day_reqs"], snap["day_tokens"],
                ),
            )

    def get_penalty(self, provider: str) -> float:
        with self._lock, self._conn() as conn:
            row = conn.execute("SELECT penalty_until FROM usage WHERE provider = ?", (provider,)).fetchone()
            return row["penalty_until"] if row else 0.0

    def set_penalty(self, provider: str, until_ts: float):
        with self._lock, self._conn() as conn:
            conn.execute(
                "INSERT INTO usage (provider, penalty_until) VALUES (?, ?)"
                " ON CONFLICT(provider) DO UPDATE SET penalty_until = ?",
                (provider, until_ts, until_ts),
            )
