from app.prompts import SYSTEM_PROMPTS, TASK_DESCRIPTIONS


def test_pyq_prompt_exists():
    assert "pyq" in SYSTEM_PROMPTS
    assert "pyq" in TASK_DESCRIPTIONS


def test_pyq_prompt_contains_guard():
    prompt = SYSTEM_PROMPTS["pyq"]
    assert "{injection_guard}" in prompt
    assert "{task_description}" in prompt
