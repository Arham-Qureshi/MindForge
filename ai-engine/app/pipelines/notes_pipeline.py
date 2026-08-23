from app.pipelines.base_pipeline import execute_chunks
from app.schemas.flashcard_schema import NotesPayload


def merge_notes_results(results: list[dict]) -> NotesPayload:
    if not results:
        return NotesPayload(document_summary="", flashcards=[], practice_exam=[])

    summaries = [r.get("document_summary", "") for r in results]
    longest_summary = max(summaries, key=len) if summaries else ""

    seen_flashcards: dict[str, dict] = {}
    for r in results:
        for fc in r.get("flashcards", []):
            key = fc["front"]
            if key not in seen_flashcards:
                seen_flashcards[key] = fc
    flashcards = list(seen_flashcards.values())

    seen_questions: dict[str, dict] = {}
    for r in results:
        for q in r.get("practice_exam", []):
            key = q["question"]
            if key not in seen_questions:
                seen_questions[key] = q
    practice_exam = list(seen_questions.values())

    return NotesPayload(
        document_summary=longest_summary,
        flashcards=flashcards,
        practice_exam=practice_exam,
    )


def process_notes(chunks: list[str]) -> NotesPayload:
    results = execute_chunks(chunks, task="notes")
    return merge_notes_results(results)
