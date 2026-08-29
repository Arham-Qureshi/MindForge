from app.prompts import SYSTEM_PROMPTS, TASK_DESCRIPTIONS


def _combined(task: str) -> str:
    return SYSTEM_PROMPTS[task] + TASK_DESCRIPTIONS.get(task, "")


def test_notes_flashcards_prompt_declares_flashcard_keys():
    p = _combined("notes_flashcards")
    assert '"flashcards"' in p
    assert '"front"' in p
    assert '"back"' in p


def test_notes_exam_prompt_declares_exam_keys():
    p = _combined("notes_exam")
    assert '"practice_exam"' in p
    assert '"question"' in p
    assert '"options"' in p


def test_notes_summary_prompt_declares_summary_keys():
    p = _combined("notes_summary")
    assert '"document_summary"' in p


def test_syllabus_prompt_declares_exact_top_level_keys():
    p = _combined("syllabus")
    for key in ('"course_title"', '"total_units"', '"learning_path"', '"priority_topics"'):
        assert key in p
    for unit_key in ('"unit_number"', '"title"', '"estimated_hours"', '"topics"', '"cognitive_level"'):
        assert unit_key in p


def test_pyq_prompt_declares_exact_top_level_keys():
    p = _combined("pyq")
    for key in ('"topic_frequency"', '"predicted_questions"'):
        assert key in p
    for q_key in ('"question"', '"bloom_level"', '"expected_marks"', '"probability_score"'):
        assert q_key in p


def test_all_prompts_mention_valid_json_only():
    for task in ("syllabus", "pyq", "notes_flashcards", "notes_exam", "notes_summary"):
        assert "valid JSON" in _combined(task)
