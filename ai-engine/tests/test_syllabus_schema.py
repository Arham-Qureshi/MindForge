import pytest
from app.schemas.syllabus_schema import SyllabusPayload, Unit, PriorityTopic


def test_syllabus_payload_valid():
    data = {
        "course_title": "Computer Science 101",
        "total_units": 3,
        "learning_path": [
            {
                "unit_number": 1,
                "title": "Introduction",
                "estimated_hours": 10,
                "topics": ["variables", "loops"],
                "cognitive_level": "Remember",
            }
        ],
        "priority_topics": [
            {"topic": "loops", "weightage": 0.6},
            {"topic": "variables", "weightage": 0.4},
        ],
    }
    payload = SyllabusPayload.model_validate(data)
    assert payload.course_title == "Computer Science 101"
    assert payload.total_units == 3
    assert len(payload.learning_path) == 1
    assert payload.learning_path[0].cognitive_level == "Remember"


def test_syllabus_payload_invalid_cognitive_level():
    data = {
        "course_title": "CS 101",
        "total_units": 1,
        "learning_path": [
            {
                "unit_number": 1,
                "title": "Intro",
                "estimated_hours": 5,
                "topics": ["topic1"],
                "cognitive_level": "InvalidLevel",
            }
        ],
        "priority_topics": [],
    }
    with pytest.raises(Exception):
        SyllabusPayload.model_validate(data)


def test_syllabus_payload_missing_fields():
    with pytest.raises(Exception):
        SyllabusPayload.model_validate({"course_title": "CS 101"})


def test_priority_topic_weightage_range():
    data = {
        "course_title": "CS 101",
        "total_units": 1,
        "learning_path": [
            {
                "unit_number": 1,
                "title": "Intro",
                "estimated_hours": 5,
                "topics": ["t1"],
                "cognitive_level": "Apply",
            }
        ],
        "priority_topics": [{"topic": "t1", "weightage": 1.5}],
    }
    with pytest.raises(Exception):
        SyllabusPayload.model_validate(data)