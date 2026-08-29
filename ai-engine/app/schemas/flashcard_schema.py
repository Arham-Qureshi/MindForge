from pydantic import BaseModel, Field
from typing import Literal


class Flashcard(BaseModel):
    front: str
    back: str
    bloom_category: Literal["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
    difficulty: Literal["Easy", "Medium", "Hard"]


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer_index: int = Field(ge=0, le=3)
    solution: str


class NotesPayload(BaseModel):
    document_summary: str
    flashcards: list[Flashcard]
    practice_exam: list[QuizQuestion]


# subtask payloads — each LLM call for notes_* returns ONLY that slice,
# but we accept missing keys with defaults so prompt-contract partials validate
class NotesFlashcardsPayload(BaseModel):
    flashcards: list[Flashcard]
    document_summary: str = ""
    practice_exam: list[QuizQuestion] = []


class NotesExamPayload(BaseModel):
    practice_exam: list[QuizQuestion]
    document_summary: str = ""
    flashcards: list[Flashcard] = []


class NotesSummaryPayload(BaseModel):
    document_summary: str
    flashcards: list[Flashcard] = []
    practice_exam: list[QuizQuestion] = []
