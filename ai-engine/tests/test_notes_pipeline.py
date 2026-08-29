from unittest.mock import patch
from app.prompts import SYSTEM_PROMPTS, TASK_DESCRIPTIONS
from app.schemas.flashcard_schema import NotesPayload
from app.pipelines.notes_pipeline import merge_notes_results, distribute_flashcards


def test_notes_prompt_exists():
    assert "notes_flashcards" in SYSTEM_PROMPTS
    assert "notes_flashcards" in TASK_DESCRIPTIONS


def test_notes_prompt_contains_guard():
    prompt = SYSTEM_PROMPTS["notes_flashcards"]
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
    merged = merge_notes_results(results, flashcard_count=10)
    assert isinstance(merged, NotesPayload)
    assert len(merged.flashcards) == 3  # RNN deduped, CNN + LSTM kept
    assert merged.document_summary == "This is a much longer and more complete summary of the lecture notes."


def test_merge_notes_truncates_to_flashcard_count():
    results = [
        {
            "document_summary": "",
            "flashcards": [
                {"front": f"Q{i}", "back": f"A{i}", "bloom_category": "Remember", "difficulty": "Easy"}
                for i in range(20)
            ],
            "practice_exam": [],
        },
    ]
    merged = merge_notes_results(results, flashcard_count=10)
    assert len(merged.flashcards) == 10


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
    merged = merge_notes_results(results, flashcard_count=10)
    assert len(merged.practice_exam) == 2  # "What is X?" deduped, "What is Y?" kept


def test_merge_notes_empty():
    merged = merge_notes_results([], flashcard_count=10)
    assert isinstance(merged, NotesPayload)
    assert merged.document_summary == ""
    assert len(merged.flashcards) == 0
    assert len(merged.practice_exam) == 0


def test_distribute_flashcards_empty():
    assert distribute_flashcards([], 10) == []


def test_distribute_flashcards_zero_count():
    assert distribute_flashcards(["a", "b"], 0) == []


def test_distribute_flashcards_single_chunk():
    assert distribute_flashcards(["chunk"], 10) == [10]


def test_distribute_flashcards_more_chunks_than_count():
    chunks = [f"chunk{i}" for i in range(8)]
    dist = distribute_flashcards(chunks, 5)
    assert len(dist) == 8
    assert sum(dist) == 5
    assert dist[:5] == [1, 1, 1, 1, 1]
    assert dist[5:] == [0, 0, 0]


def test_distribute_flashcards_proportional():
    chunks = ["a " * 2000, "b " * 1000, "c " * 500]
    dist = distribute_flashcards(chunks, 10)
    assert len(dist) == 3
    assert sum(dist) == 10
    assert all(d >= 1 for d in dist)
    assert dist[0] > dist[1] > dist[2]


def test_distribute_flashcards_equal_chunks():
    chunks = ["same"] * 4
    dist = distribute_flashcards(chunks, 10)
    assert sum(dist) == 10
    assert len(dist) == 4


def test_distribute_flashcards_exact_fit():
    chunks = ["a", "b", "c"]
    dist = distribute_flashcards(chunks, 3)
    assert dist == [1, 1, 1]


def test_distribute_flashcards_large_total():
    chunks = ["x " * 100, "y " * 200]
    dist = distribute_flashcards(chunks, 15)
    assert sum(dist) == 15
    assert dist[0] < dist[1]
