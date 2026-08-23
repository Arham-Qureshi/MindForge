from app.prompts import SYSTEM_PROMPTS, TASK_DESCRIPTIONS


def test_notes_prompt_exists():
    assert "notes" in SYSTEM_PROMPTS
    assert "notes" in TASK_DESCRIPTIONS


def test_notes_prompt_contains_guard():
    prompt = SYSTEM_PROMPTS["notes"]
    assert "{injection_guard}" in prompt
    assert "{task_description}" in prompt
