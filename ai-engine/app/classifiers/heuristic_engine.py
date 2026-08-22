import re
from pydantic import BaseModel
from typing import Literal

from app.classifiers.regex_patterns import SYLLABUS_PATTERNS, PYQ_PATTERNS, NOTES_PATTERNS
from app.classifiers.score_calculator import calculate_scores

MAX_INPUT_CHARS = 5000


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


def classify_document(text_sample: str) -> ClassificationResult:
    text = text_sample[:MAX_INPUT_CHARS].lower()

    s_count = _count_matches(text, "SYLLABUS")
    p_count = _count_matches(text, "PYQ")
    n_count = _count_matches(text, "NOTES")

    result = calculate_scores(s_count, p_count, n_count)

    return ClassificationResult(
        doc_type=result["winner"],
        confidence=result["confidence"],
        metrics=result["metrics"],
    )
