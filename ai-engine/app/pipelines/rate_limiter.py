import threading
import time

MINUTE = 60.0
DAY = 86400.0

PROVIDER_LIMITS = {
    "groq": {"rpm": 30, "tpm": 8000, "rpd": 1000, "tpd": 200000},
    "gemini": {"rpm": 15, "tpm": 250000, "rpd": 1000, "tpd": None},
}


class DailyQuotaExhausted(Exception):
    def __init__(self, provider: str, reset_at: float):
        self.provider = provider
        self.reset_at = reset_at
        super().__init__(
            f"{provider} daily free quota exhausted; resets at {reset_at}"
        )


class RateLimiter:
    """Pre-send gate backed by persisted counters so quota truth survives restarts."""

    def __init__(self, store, clock=time.time, sleeper=time.sleep):
        self.store = store
        self._clock = clock
        self._sleep = sleeper
        # reservations happen on the calling thread; keep deltas consistent
        self._lock = threading.Lock()
        self._reserved = {}

    def acquire(self, provider: str, est_tokens: int) -> None:
        limits = PROVIDER_LIMITS[provider]
        if est_tokens >= limits["tpm"]:
            raise ValueError(
                f"request estimate ({est_tokens}) exceeds {provider} TPM budget"
            )

        while True:
            wait = self._try_acquire(provider, est_tokens)
            if wait is None:
                with self._lock:
                    self._reserved[provider] = est_tokens
                return None
            self._sleep(wait)

    def record_usage(self, provider: str, actual_tokens: int):
        now = self._clock()
        with self._lock:
            reserved = self._reserved.pop(provider, 0)
            delta = actual_tokens - reserved
            snap = self.store.snapshot(provider)
            if now - snap["win_start"] < MINUTE and snap["win_start"] > 0:
                snap["tokens"] = max(0, snap["tokens"] + delta)
                snap["day_tokens"] = max(0, snap["day_tokens"] + delta)
                self.store.save_snapshot(provider, snap)

    def headroom(self, provider: str) -> dict:
        # live view for batch packing — no side effects
        now = self._clock()
        penalty_until = self.store.get_penalty(provider)
        if penalty_until > now:
            return {"rpm_rem": 0, "tpm_rem": 0, "reset_in": penalty_until - now, "penalized": True}
        with self._lock:
            snap = self.store.snapshot(provider)
            win_start = int(now // MINUTE) * MINUTE
            # if window rolled, counters are logically zero
            if snap["win_start"] != win_start:
                snap["reqs"] = 0
                snap["tokens"] = 0
            day_start = int(now // DAY) * DAY
            if snap["day_start"] != day_start:
                snap["day_reqs"] = 0
                snap["day_tokens"] = 0
            limits = PROVIDER_LIMITS[provider]
            rpm_rem = max(0, limits["rpm"] - snap["reqs"])
            tpm_rem = max(0, limits["tpm"] - snap["tokens"])
            reset_in = (win_start + MINUTE) - now
            return {"rpm_rem": rpm_rem, "tpm_rem": tpm_rem, "reset_in": reset_in, "penalized": False}

    def _try_acquire(self, provider: str, est_tokens: int) -> float | None:
        now = self._clock()
        penalty_until = self.store.get_penalty(provider)
        if penalty_until > now:
            return penalty_until - now

        with self._lock:
            snap = self.store.snapshot(provider)
            win_start = int(now // MINUTE) * MINUTE
            if snap["win_start"] != win_start:
                snap["win_start"] = win_start
                snap["reqs"] = 0
                snap["tokens"] = 0
            day_start = int(now // DAY) * DAY
            if snap["day_start"] != day_start:
                snap["day_start"] = day_start
                snap["day_reqs"] = 0
                snap["day_tokens"] = 0

            limits = PROVIDER_LIMITS[provider]
            day_reset_at = day_start + DAY

            if limits["rpd"] is not None and snap["day_reqs"] + 1 > limits["rpd"]:
                raise DailyQuotaExhausted(provider, day_reset_at)
            if limits["tpd"] is not None and snap["day_tokens"] + est_tokens > limits["tpd"]:
                raise DailyQuotaExhausted(provider, day_reset_at)

            window_reset_at = win_start + MINUTE
            if snap["reqs"] + 1 > limits["rpm"]:
                return max(0.5, window_reset_at - now)
            if snap["tokens"] + est_tokens > limits["tpm"]:
                return max(0.5, window_reset_at - now)

            snap["reqs"] += 1
            snap["tokens"] += est_tokens
            snap["day_reqs"] += 1
            snap["day_tokens"] += est_tokens
            self.store.save_snapshot(provider, snap)
            return None
