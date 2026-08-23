import pytest
from app.schemas.flashcard_schema import Flashcard, QuizQuestion, NotesPayload


def test_notes_payload_valid():
    data = {
        "document_summary": "DBMS chapter covers normalization and transactions.",
        "flashcards": [
            {"front": "What is 1NF?", "back": "A relation is in 1NF if all attributes are atomic.", "bloom_category": "Remember", "difficulty": "Easy"},
            {"front": "Explain ACID", "back": "Atomicity, Consistency, Isolation, Durability.", "bloom_category": "Understand", "difficulty": "Medium"},
        ],
        "practice_exam": [
            {
                "question": "Which normal form removes transitive dependencies?",
                "options": ["1NF", "2NF", "3NF", "BCNF"],
                "correct_answer_index": 2,
                "solution": "3NF eliminates transitive dependencies.",
            }
        ],
    }
    payload = NotesPayload.model_validate(data)
    assert payload.document_summary == "DBMS chapter covers normalization and transactions."
    assert len(payload.flashcards) == 2
    assert payload.flashcards[0].bloom_category == "Remember"
    assert len(payload.practice_exam) == 1
    assert payload.practice_exam[0].correct_answer_index == 2


def test_notes_payload_empty_lists():
    data = {"document_summary": "Empty", "flashcards": [], "practice_exam": []}
    payload = NotesPayload.model_validate(data)
    assert len(payload.flashcards) == 0
    assert len(payload.practice_exam) == 0


def test_flashcard_invalid_bloom_category():
    data = {
        "document_summary": "Test",
        "flashcards": [{"front": "Q?", "back": "A.", "bloom_category": "InvalidLevel", "difficulty": "Easy"}],
        "practice_exam": [],
    }
    with pytest.raises(Exception):
        NotesPayload.model_validate(data)


def test_flashcard_invalid_difficulty():
    data = {
        "document_summary": "Test",
        "flashcards": [{"front": "Q?", "back": "A.", "bloom_category": "Remember", "difficulty": "Impossible"}],
        "practice_exam": [],
    }
    with pytest.raises(Exception):
        NotesPayload.model_validate(data)


def test_notes_payload_missing_required_fields():
    with pytest.raises(Exception):
        NotesPayload.model_validate({})


def test_quiz_question_invalid_options_count():
    data = {
        "document_summary": "Test",
        "flashcards": [],
        "practice_exam": [
            {"question": "Q?", "options": ["A", "B", "C"], "correct_answer_index": 0, "solution": "Sol"}
        ],
    }
    with pytest.raises(Exception):
        NotesPayload.model_validate(data)


def test_quiz_question_invalid_correct_index():
    data = {
        "document_summary": "Test",
        "flashcards": [],
        "practice_exam": [
            {"question": "Q?", "options": ["A", "B", "C", "D"], "correct_answer_index": 5, "solution": "Sol"}
        ],
    }
    with pytest.raises(Exception):
        NotesPayload.model_validate(data)
