import json

import pytest

from app.app import create_app
from app.jobs.store import Store
from app.jobs.worker import Worker
from app.pipelines.llm_client import LLMResult


class FakeLimiterStore:
    def set_penalty(self, provider, until_ts):
        pass


class FakeLimiter:
    def __init__(self):
        self.store = FakeLimiterStore()

    def acquire(self, provider, est_tokens):
        pass

    def record_usage(self, provider, actual_tokens):
        pass


class FakeLLM:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)

    def estimate_request_tokens(self, task, user):
        return 100

    def complete(self, task, user, model=None, json_mode=False):
        outcome = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if isinstance(outcome, Exception):
            raise outcome
        return LLMResult(json.dumps(outcome), 100)


VALID_PAYLOADS = {
    "SYLLABUS": {"course_title": "DS", "total_units": 5, "learning_path": [], "priority_topics": []},
    "PYQ": {"topic_frequency": [], "predicted_questions": []},
    "NOTES": {"document_summary": "ok", "flashcards": [], "practice_exam": []},
}


@pytest.fixture()
def make_client(tmp_path):
    def _make(llm_outcomes):
        store = Store(str(tmp_path / "jobs.db"))
        worker = Worker(store, limiter=FakeLimiter(), llm=FakeLLM(llm_outcomes))
        app = create_app(store=store, worker=worker)
        from fastapi.testclient import TestClient
        return TestClient(app)

    return _make
