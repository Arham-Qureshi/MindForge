from unittest.mock import patch
from app.prompts import SYSTEM_PROMPTS, TASK_DESCRIPTIONS
from app.schemas.flashcard_schema import NotesPayload
from app.pipelines.notes_pipeline import process_notes, merge_notes_results


def test_notes_prompt_exists():
    assert "notes" in SYSTEM_PROMPTS
    assert "notes" in TASK_DESCRIPTIONS


def test_notes_prompt_contains_guard():
    prompt = SYSTEM_PROMPTS["notes"]
    assert "{injection_guard}" in prompt
    assert "{task_description}" in prompt


def test_merge_notes_combines_flashcards():
    results = [
        {
            "document_summary": "Short summary.",
            "flashcards": [
                {"front": "RNN", "back": "Recurrent Neural Network", "bloom_category": "Remember", "difficulty": "Medium"},
                {"front": "CNN", "back": "Convolutional Neural Network", "bloom_category": "Remember", "difficulty": "Easy"},
            ],
            "practice_exam": [],
        },
        {
            "document_summary": "This is a much longer and more complete summary of the lecture notes.",
            "flashcards": [
                {"front": "RNN", "back": "Recurrent Neural Network", "bloom_category": "Remember", "difficulty": "Medium"},
                {"front": "LSTM", "back": "Long Short-Term Memory", "bloom_category": "Understand", "difficulty": "Hard"},
            ],
            "practice_exam": [
                {"question": "What is backprop?", "options": ["A", "B", "C", "D"], "correct_answer_index": 1, "solution": "Explanation"},
            ],
        },
    ]
    merged = merge_notes_results(results)
    assert isinstance(merged, NotesPayload)
    assert len(merged.flashcards) == 3  # RNN deduped, CNN + LSTM kept
    assert merged.document_summary == "This is a much longer and more complete summary of the lecture notes."


def test_merge_notes_deduplicates_quiz_questions():
    results = [
        {
            "document_summary": "",
            "flashcards": [],
            "practice_exam": [
                {"question": "What is X?", "options": ["A", "B", "C", "D"], "correct_answer_index": 0, "solution": "Sol1"},
            ],
        },
        {
            "document_summary": "",
            "flashcards": [],
            "practice_exam": [
                {"question": "What is X?", "options": ["A", "B", "C", "D"], "correct_answer_index": 2, "solution": "Sol2"},
                {"question": "What is Y?", "options": ["A", "B", "C", "D"], "correct_answer_index": 1, "solution": "Sol3"},
            ],
        },
    ]
    merged = merge_notes_results(results)
    assert len(merged.practice_exam) == 2  # "What is X?" deduped, "What is Y?" kept


def test_merge_notes_empty():
    merged = merge_notes_results([])
    assert isinstance(merged, NotesPayload)
    assert merged.document_summary == ""
    assert len(merged.flashcards) == 0
    assert len(merged.practice_exam) == 0


def test_process_notes_returns_payload():
    with patch("app.pipelines.notes_pipeline.execute_chunks") as mock_exec:
        mock_exec.return_value = [
            {
                "document_summary": "Test summary",
                "flashcards": [
                    {"front": "Term", "back": "Def", "bloom_category": "Remember", "difficulty": "Easy"}
                ],
                "practice_exam": [
                    {"question": "Q1?", "options": ["A", "B", "C", "D"], "correct_answer_index": 0, "solution": "Sol"}
                ],
            }
        ]
        result = process_notes(["chunk1"])
        assert isinstance(result, NotesPayload)
        assert result.document_summary == "Test summary"
        assert len(result.flashcards) == 1
        assert len(result.practice_exam) == 1
