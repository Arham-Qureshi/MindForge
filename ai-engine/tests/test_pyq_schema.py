import pytest
from app.schemas.pyq_schema import PYQAnalysisPayload, TopicFrequency, PredictedQuestion


def test_pyq_payload_valid():
    data = {
        "topic_frequency": [
            {"topic": "Normalization", "percentage": 0.35, "question_count": 7},
            {"topic": "Transactions", "percentage": 0.25, "question_count": 5},
        ],
        "predicted_questions": [
            {
                "question": "Design a 3NF schema for an employee database with department dependencies.",
                "bloom_level": "Apply",
                "expected_marks": 10,
                "probability_score": 0.87,
            }
        ],
    }
    payload = PYQAnalysisPayload.model_validate(data)
    assert len(payload.topic_frequency) == 2
    assert payload.topic_frequency[0].topic == "Normalization"
    assert payload.predicted_questions[0].bloom_level == "Apply"


def test_pyq_payload_empty_lists():
    data = {"topic_frequency": [], "predicted_questions": []}
    payload = PYQAnalysisPayload.model_validate(data)
    assert len(payload.topic_frequency) == 0
    assert len(payload.predicted_questions) == 0


def test_pyq_payload_invalid_bloom_level():
    data = {
        "topic_frequency": [],
        "predicted_questions": [
            {
                "question": "Describe X",
                "bloom_level": "Remember",
                "expected_marks": 5,
                "probability_score": 0.5,
            }
        ],
    }
    with pytest.raises(Exception):
        PYQAnalysisPayload.model_validate(data)


def test_pyq_payload_missing_required_fields():
    with pytest.raises(Exception):
        PYQAnalysisPayload.model_validate({})


def test_topic_frequency_percentage_range():
    data = {
        "topic_frequency": [{"topic": "X", "percentage": 1.5, "question_count": 1}],
        "predicted_questions": [],
    }
    with pytest.raises(Exception):
        PYQAnalysisPayload.model_validate(data)


def test_predicted_question_probability_range():
    data = {
        "topic_frequency": [],
        "predicted_questions": [
            {
                "question": "Q?",
                "bloom_level": "Analyze",
                "expected_marks": 5,
                "probability_score": 2.0,
            }
        ],
    }
    with pytest.raises(Exception):
        PYQAnalysisPayload.model_validate(data)
