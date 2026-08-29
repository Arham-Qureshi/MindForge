import re
import numpy as np
from pydantic import BaseModel
from typing import Literal

from app.classifiers.regex_patterns import SYLLABUS_PATTERNS, PYQ_PATTERNS, NOTES_PATTERNS
from app.classifiers.score_calculator import calculate_scores

MAX_INPUT_CHARS = 5000

# hybrid fallback — uses same fastembed model as chunker (BAAI/bge-small-en-v1.5) when regex is low-confidence
_embedding_model = None
_centroids: dict[str, np.ndarray] | None = None

_REPRESENTATIVES = {
    "SYLLABUS": "Module 1 Unit 1 Course Outcomes Syllabus Curriculum Credits Prerequisites Grading Course Content",
    "PYQ": "Q.1 Question 1 [10 marks] Time: 3 hours Attempt any Section A Previous year Exam",
    "NOTES": "Definition Introduction Chapter Topic Study Process Function Structure Theory Important Concept Example Diagram Figure Overview Note Summary",
}


class ClassMetrics(BaseModel):
    count: int
    matched_markers: list[str]


class ClassificationResult(BaseModel):
    doc_type: Literal["SYLLABUS", "PYQ", "NOTES"]
    confidence: float
    metrics: dict[str, ClassMetrics]


def _compile_category(patterns: list[str]) -> re.Pattern:
    combined = "|".join(f"(?:{p})" for p in patterns)
    return re.compile(combined, re.IGNORECASE | re.ASCII)


_COMBINED = {
    "SYLLABUS": _compile_category(SYLLABUS_PATTERNS),
    "PYQ": _compile_category(PYQ_PATTERNS),
    "NOTES": _compile_category(NOTES_PATTERNS),
}


def _count_matches(text: str, category: str) -> int:
    return len(_COMBINED[category].findall(text))


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from fastembed import TextEmbedding

            _embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        except Exception:
            _embedding_model = None
    return _embedding_model


def _get_centroids() -> dict[str, np.ndarray] | None:
    global _centroids
    if _centroids is not None:
        return _centroids
    model = _get_embedding_model()
    if model is None:
        return None
    try:
        vecs = {}
        for label, rep in _REPRESENTATIVES.items():
            emb = list(model.embed([rep]))[0]
            vecs[label] = np.array(emb)
        _centroids = vecs
        return _centroids
    except Exception:
        return None


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def _classify_via_embedding(text: str) -> tuple[str, float] | None:
    model = _get_embedding_model()
    cents = _get_centroids()
    if model is None or cents is None:
        return None
    try:
        q = np.array(list(model.embed([text[:2000]]))[0])
        scores = {label: _cosine(q, vec) for label, vec in cents.items()}
        winner = max(scores, key=scores.get)  # type: ignore
        # confidence as margin between top 2
        sorted_vals = sorted(scores.values(), reverse=True)
        margin = sorted_vals[0] - sorted_vals[1] if len(sorted_vals) > 1 else 1.0
        # map cosine 0.7-0.95 to confidence 0.6-0.95
        conf = 0.6 + margin * 0.8
        conf = max(0.6, min(0.95, conf))
        return winner, conf
    except Exception:
        return None


def classify_document(text_sample: str) -> ClassificationResult:
    text = text_sample[:MAX_INPUT_CHARS].lower()

    s_count = _count_matches(text, "SYLLABUS")
    p_count = _count_matches(text, "PYQ")
    n_count = _count_matches(text, "NOTES")

    result = calculate_scores(s_count, p_count, n_count)

    # hybrid fallback when regex is low-confidence (0% tie or weak signal) — skip for empty/short
    stripped_len = len(text_sample.strip())
    needs_fallback = (result["confidence"] == 0.0 or result["confidence"] < 0.55) and stripped_len > 30
    if needs_fallback:
        emb = _classify_via_embedding(text_sample[:2000])
        if emb:
            winner, conf = emb
            # keep regex metrics for transparency but override winner/confidence
            return ClassificationResult(
                doc_type=winner,  # type: ignore
                confidence=conf,
                metrics=result["metrics"],
            )

    return ClassificationResult(
        doc_type=result["winner"],
        confidence=result["confidence"],
        metrics=result["metrics"],
    )
