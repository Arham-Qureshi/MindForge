from unittest.mock import patch
from app.prompts import SYSTEM_PROMPTS, TASK_DESCRIPTIONS
from app.schemas.pyq_schema import PYQAnalysisPayload
from app.pipelines.pyq_pipeline import process_pyq, merge_pyq_results


def test_pyq_prompt_exists():
    assert "pyq" in SYSTEM_PROMPTS
    assert "pyq" in TASK_DESCRIPTIONS


def test_pyq_prompt_contains_guard():
    prompt = SYSTEM_PROMPTS["pyq"]
    assert "{injection_guard}" in prompt
    assert "{task_description}" in prompt


def test_merge_pyq_results_combines_topics():
    results = [
        {
            "topic_frequency": [
                {"topic": "Normalization", "percentage": 0.3, "question_count": 3},
                {"topic": "Transactions", "percentage": 0.2, "question_count": 2},
            ],
            "predicted_questions": [
                {"question": "Q1 Apply", "bloom_level": "Apply", "expected_marks": 5, "probability_score": 0.8}
            ],
        },
        {
            "topic_frequency": [
                {"topic": "Normalization", "percentage": 0.4, "question_count": 4},
                {"topic": "Indexing", "percentage": 0.3, "question_count": 3},
            ],
            "predicted_questions": [
                {"question": "Q2 Analyze", "bloom_level": "Analyze", "expected_marks": 10, "probability_score": 0.9},
                {"question": "Q1 Apply", "bloom_level": "Apply", "expected_marks": 5, "probability_score": 0.7},
            ],
        },
    ]
    merged = merge_pyq_results(results)
    assert isinstance(merged, PYQAnalysisPayload)
    topic_names = {t.topic for t in merged.topic_frequency}
    assert "Normalization" in topic_names
    assert "Transactions" in topic_names
    assert "Indexing" in topic_names


def test_merge_pyq_results_deduplicates_questions():
    results = [
        {
            "topic_frequency": [],
            "predicted_questions": [
                {"question": "Same question", "bloom_level": "Apply", "expected_marks": 5, "probability_score": 0.6},
                {"question": "Different question", "bloom_level": "Analyze", "expected_marks": 10, "probability_score": 0.7},
            ],
        },
        {
            "topic_frequency": [],
            "predicted_questions": [
                {"question": "Same question", "bloom_level": "Apply", "expected_marks": 5, "probability_score": 0.9},
            ],
        },
    ]
    merged = merge_pyq_results(results)
    assert len(merged.predicted_questions) == 2
    same_q = [p for p in merged.predicted_questions if p.question == "Same question"]
    assert same_q[0].probability_score == 0.9


def test_merge_pyq_results_empty():
    merged = merge_pyq_results([])
    assert isinstance(merged, PYQAnalysisPayload)
    assert len(merged.topic_frequency) == 0
    assert len(merged.predicted_questions) == 0


def test_process_pyq_returns_payload():
    with patch("app.pipelines.pyq_pipeline.execute_chunks") as mock_exec:
        mock_exec.return_value = [
            {
                "topic_frequency": [{"topic": "SQL", "percentage": 0.5, "question_count": 5}],
                "predicted_questions": [
                    {"question": "Apply SQL", "bloom_level": "Apply", "expected_marks": 5, "probability_score": 0.8}
                ],
            }
        ]
        result = process_pyq(["chunk1"])
        assert isinstance(result, PYQAnalysisPayload)
        assert len(result.topic_frequency) == 1
        assert len(result.predicted_questions) == 1
