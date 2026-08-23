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
