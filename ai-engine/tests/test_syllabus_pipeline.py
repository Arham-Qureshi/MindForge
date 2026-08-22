from unittest.mock import patch
from app.schemas.syllabus_schema import SyllabusPayload
from app.pipelines.syllabus_pipeline import process_syllabus, merge_syllabus_results
from app.prompts import SYSTEM_PROMPTS, TASK_DESCRIPTIONS


def test_syllabus_prompt_exists():
    assert "syllabus" in SYSTEM_PROMPTS
    assert "syllabus" in TASK_DESCRIPTIONS


def test_syllabus_prompt_contains_guard():
    from app.prompts import INJECTION_GUARD
    prompt = SYSTEM_PROMPTS["syllabus"]
    assert "{injection_guard}" in prompt
    assert "{task_description}" in prompt


def test_merge_syllabus_results_combines_units():
    results = [
        {
            "course_title": "CS 101",
            "total_units": 2,
            "learning_path": [
                {"unit_number": 1, "title": "Intro", "estimated_hours": 5, "topics": ["t1"], "cognitive_level": "Remember"}
            ],
            "priority_topics": [{"topic": "t1", "weightage": 0.5}],
        },
        {
            "course_title": "CS 101",
            "total_units": 2,
            "learning_path": [
                {"unit_number": 2, "title": "Advanced", "estimated_hours": 8, "topics": ["t2"], "cognitive_level": "Apply"}
            ],
            "priority_topics": [{"topic": "t2", "weightage": 0.5}],
        },
    ]
    merged = merge_syllabus_results(results)
    assert merged.total_units == 2
    assert len(merged.learning_path) == 2
    assert len(merged.priority_topics) == 2


def test_merge_syllabus_results_single():
    results = [
        {
            "course_title": "CS 101",
            "total_units": 1,
            "learning_path": [
                {"unit_number": 1, "title": "Intro", "estimated_hours": 5, "topics": ["t1"], "cognitive_level": "Remember"}
            ],
            "priority_topics": [{"topic": "t1", "weightage": 1.0}],
        }
    ]
    merged = merge_syllabus_results(results)
    assert merged.course_title == "CS 101"
    assert len(merged.learning_path) == 1


def test_process_syllabus_returns_payload():
    with patch("app.pipelines.syllabus_pipeline.execute_chunks") as mock_exec:
        mock_exec.return_value = [
            {
                "course_title": "CS 101",
                "total_units": 1,
                "learning_path": [
                    {"unit_number": 1, "title": "Intro", "estimated_hours": 5, "topics": ["t1"], "cognitive_level": "Remember"}
                ],
                "priority_topics": [{"topic": "t1", "weightage": 1.0}],
            }
        ]
        result = process_syllabus(["chunk1"])
        assert isinstance(result, SyllabusPayload)
        assert result.course_title == "CS 101"
