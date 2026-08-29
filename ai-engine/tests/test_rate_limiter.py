import pytest

from app.jobs.store import Store
from app.pipelines.rate_limiter import (
    RateLimiter,
    PROVIDER_LIMITS,
    DailyQuotaExhausted,
)


class FakeClock:
    def __init__(self):
        self.t = 1_700_000_000.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


@pytest.fixture()
def env(tmp_path):
    store = Store(str(tmp_path / "jobs.db"))
    clock = FakeClock()
    limiter = RateLimiter(store, clock=clock, sleeper=clock.advance)
    return limiter, clock


def seed_snapshot(store, provider, clock, **fields):
    snap = store.snapshot(provider)
    snap["win_start"] = int(clock() // 60) * 60
    snap["day_start"] = int(clock() // 86400) * 86400
    snap.update(fields)
    store.save_snapshot(provider, snap)


def test_limits_match_free_tier():
    assert PROVIDER_LIMITS["groq"] == {"rpm": 30, "tpm": 8000, "rpd": 1000, "tpd": 200000}
    assert PROVIDER_LIMITS["gemini"]["rpm"] == 15


def test_acquire_ok_first_call(env):
    rl, _ = env
    assert rl.acquire("groq", 3000) is None


def test_rpm_blocks_until_window_reset(env):
    rl, clock = env
    for _ in range(PROVIDER_LIMITS["groq"]["rpm"]):
        assert rl.acquire("groq", 10) is None

    # 31st call must sleep across the minute boundary before succeeding
    t0 = clock.t
    assert rl.acquire("groq", 10) is None
    assert clock.t - t0 >= 30
    # new window rolled, so the request landed as the first of the fresh minute
    assert rl.store.snapshot("groq")["reqs"] == 1


def test_tpm_blocks_when_minute_budget_exhausted(env):
    rl, clock = env
    assert rl.acquire("groq", 7500) is None

    t0 = clock.t
    assert rl.acquire("groq", 1000) is None
    assert clock.t - t0 >= 30


def test_tpd_exhaustion_raises_daily_quota(env):
    rl, clock = env
    seed_snapshot(rl.store, "groq", clock, day_tokens=195000, day_reqs=50)
    with pytest.raises(DailyQuotaExhausted):
        rl.acquire("groq", 6000)


def test_rpd_exhaustion_raises_daily_quota(env):
    rl, clock = env
    seed_snapshot(rl.store, "gemini", clock, day_reqs=PROVIDER_LIMITS["gemini"]["rpd"])
    with pytest.raises(DailyQuotaExhausted):
        rl.acquire("gemini", 5)


def test_day_window_roll_resets_quota(env):
    rl, clock = env
    seed_snapshot(rl.store, "gemini", clock, day_reqs=PROVIDER_LIMITS["gemini"]["rpd"], day_start=0)
    assert rl.acquire("gemini", 5) is None


def test_penalty_blocks_acquire_until_cleared(env):
    rl, clock = env
    rl.store.set_penalty("groq", clock() + 120)
    t0 = clock.t
    assert rl.acquire("groq", 10) is None
    assert clock.t - t0 >= 119


def test_record_usage_reconciles_reservation(env):
    rl, clock = env
    assert rl.acquire("groq", 3000) is None
    rl.record_usage("groq", actual_tokens=2100)
    snap = rl.store.snapshot("groq")
    assert snap["tokens"] == 2100
    assert snap["reqs"] == 1


def test_counters_persist_across_limiter_instances(tmp_path):
    store_path = str(tmp_path / "jobs.db")
    clock = FakeClock()

    rl1 = RateLimiter(Store(store_path), clock=clock, sleeper=clock.advance)
    assert rl1.acquire("groq", 7500) is None
    assert Store(store_path).snapshot("groq")["tokens"] == 7500

    # second instance sees the persisted reservation -> must block across boundary
    t0 = clock.t
    rl2 = RateLimiter(Store(store_path), clock=clock, sleeper=clock.advance)
    assert rl2.acquire("groq", 1000) is None
    assert clock.t - t0 >= 30


def test_est_over_budget_rejected_immediately(env):
    rl, _ = env
    with pytest.raises(ValueError):
        rl.acquire("groq", PROVIDER_LIMITS["groq"]["tpm"] + 1)
