import pytest
from app.classifiers.regex_patterns import (
    SYLLABUS_PATTERNS,
    PYQ_PATTERNS,
    NOTES_PATTERNS,
)


def test_syllabus_patterns_is_list():
    assert isinstance(SYLLABUS_PATTERNS, list)
    assert len(SYLLABUS_PATTERNS) > 0


def test_pyq_patterns_is_list():
    assert isinstance(PYQ_PATTERNS, list)
    assert len(PYQ_PATTERNS) > 0


def test_notes_patterns_is_list():
    assert isinstance(NOTES_PATTERNS, list)
    assert len(NOTES_PATTERNS) > 0


def test_all_patterns_are_strings():
    for p in SYLLABUS_PATTERNS + PYQ_PATTERNS + NOTES_PATTERNS:
        assert isinstance(p, str)


def test_syllabus_patterns_match_module():
    import re
    text = "module 3 advanced topics"
    matches = [m for p in SYLLABUS_PATTERNS for m in re.findall(p, text, re.IGNORECASE)]
    assert len(matches) > 0


def test_pyq_patterns_match_question():
    import re
    text = "q.1 Explain the following"
    matches = [m for p in PYQ_PATTERNS for m in re.findall(p, text, re.IGNORECASE)]
    assert len(matches) > 0


def test_notes_patterns_match_definition():
    import re
    text = "definition: A variable is a named storage location"
    matches = [m for p in NOTES_PATTERNS for m in re.findall(p, text, re.IGNORECASE)]
    assert len(matches) > 0


from app.classifiers.score_calculator import calculate_scores


def test_calculate_scores_syllabus_wins():
    result = calculate_scores(10, 3, 2)
    assert result["winner"] == "SYLLABUS"
    assert result["confidence"] == pytest.approx(10 / 15)


def test_calculate_scores_pyq_wins():
    result = calculate_scores(2, 8, 3)
    assert result["winner"] == "PYQ"
    assert result["confidence"] == pytest.approx(8 / 13)


def test_calculate_scores_notes_wins():
    result = calculate_scores(1, 1, 9)
    assert result["winner"] == "NOTES"
    assert result["confidence"] == pytest.approx(9 / 11)


def test_calculate_scores_tie_defaults_to_notes():
    result = calculate_scores(5, 5, 3)
    assert result["winner"] == "NOTES"


def test_calculate_scores_all_zero():
    result = calculate_scores(0, 0, 0)
    assert result["winner"] == "NOTES"
    assert result["confidence"] == 0.0


def test_calculate_scores_equal_counts():
    result = calculate_scores(4, 4, 4)
    assert result["winner"] == "NOTES"
    assert result["confidence"] == pytest.approx(4 / 12)


def test_calculate_scores_has_metrics():
    result = calculate_scores(6, 2, 1)
    assert "SYLLABUS" in result["metrics"]
    assert "PYQ" in result["metrics"]
    assert "NOTES" in result["metrics"]
    assert result["metrics"]["SYLLABUS"]["count"] == 6


from app.classifiers.heuristic_engine import classify_document


def test_classify_syllabus_document():
    text = """
    Module 1: Introduction
    Course Outcomes: After completing this module, students will be able to
    Understand the fundamentals. Credits: 4. Prerequisites: None.
    Grading: Internal 40%, External 60%. Unit 1 covers basic concepts.
    Syllabus overview for the semester. Curriculum design principles.
    """
    result = classify_document(text)
    assert result.doc_type == "SYLLABUS"
    assert 0.0 <= result.confidence <= 1.0
    assert "SYLLABUS" in result.metrics


def test_classify_pyq_document():
    text = """
    q.1 What is inheritance? [10 marks]
    q.2 Explain polymorphism with example. [15 marks]
    q.3 Define method overloading. [5 marks]
    Time: 3 hours. Attempt any question from each section.
    Section A: q.1 or q.2. Section B: q.3 or q.4.
    Previous year question paper 2024.
    """
    result = classify_document(text)
    assert result.doc_type == "PYQ"
    assert 0.0 <= result.confidence <= 1.0


def test_classify_notes_document():
    text = """
    Definition: A algorithm is a step-by-step procedure for solving a problem.
    Overview: This chapter covers the basic concepts of data structures.
    For example, consider a linked list implementation.
    Therefore, we can conclude that arrays are more efficient for indexing.
    In summary, time complexity analysis is crucial for algorithm design.
    Notes: These are important topics for examination.
    Chapter 1: Introduction to Algorithms. Topic: Big-O Notation.
    """
    result = classify_document(text)
    assert result.doc_type == "NOTES"
    assert 0.0 <= result.confidence <= 1.0


def test_classify_empty_text():
    result = classify_document("")
    assert result.doc_type == "NOTES"
    assert result.confidence == 0.0


def test_classify_short_text():
    result = classify_document("Hello world")
    assert result.doc_type == "NOTES"
    assert result.confidence == 0.0


def test_classify_returns_classification_result():
    from pydantic import BaseModel
    result = classify_document("module 1 course outcomes credits")
    assert isinstance(result, BaseModel)
    assert hasattr(result, "doc_type")
    assert hasattr(result, "confidence")
    assert hasattr(result, "metrics")
