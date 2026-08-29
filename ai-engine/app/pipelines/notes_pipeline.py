from app.pipelines.base_pipeline import execute_chunks
from app.pipelines.tokens import count_tokens
from app.schemas.flashcard_schema import NotesPayload


def distribute_flashcards(chunks: list[str], total: int) -> list[int]:
    """Distribute flashcard count proportionally by token length.

    Guarantees:
    - Every chunk gets at least 1 (no topic skipped)
    - Sum of distribution equals total
    - Larger chunks receive more flashcards
    """
    if not chunks or total <= 0:
        return []
    if len(chunks) == 1:
        return [total]
    if len(chunks) >= total:
        dist = [1] * total
        dist.extend([0] * (len(chunks) - total))
        return dist

    token_counts = [max(count_tokens(c), 1) for c in chunks]
    total_tokens = sum(token_counts)
    raw = [total * tc / total_tokens for tc in token_counts]

    floored = [int(r) for r in raw]
    remainders = [(raw[i] - floored[i], i) for i in range(len(chunks))]
    remainder = total - sum(floored)

    remainders.sort(key=lambda x: -x[0])
    for i in range(remainder):
        floored[remainders[i][1]] += 1

    return floored


def merge_notes_results(results: list[dict], flashcard_count: int = 10) -> NotesPayload:
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

    if len(flashcards) > flashcard_count:
        flashcards = flashcards[:flashcard_count]

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
