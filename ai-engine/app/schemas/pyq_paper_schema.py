from pydantic import BaseModel, Field
from typing import Literal


class BlueprintRow(BaseModel):
    topic: str
    percentage: float = Field(ge=0.0, le=1.0)
    question_count: int
    marks: int
    bloom_breakdown: dict[str, int] = Field(default_factory=dict)


class BlueprintPayload(BaseModel):
    total_marks: int = 80
    rows: list[BlueprintRow]


class ExamSection(BaseModel):
    name: str
    instructions: str
    questions: list[str]  # question texts with metadata in parent? keep simple for now
    # we will store full predicted questions inside


class ExamPaperQuestion(BaseModel):
    question: str
    topic: str
    bloom_level: Literal["Apply", "Analyze", "Evaluate"]
    expected_marks: int
    probability_score: float = Field(ge=0.0, le=1.0)
    q_no: int


class ExamPaperSection(BaseModel):
    name: str  # Section A, Section B
    instructions: str  # Attempt any 3 of 5 etc.
    questions: list[ExamPaperQuestion]


class ExamPaper(BaseModel):
    title: str
    time: str  # 3 Hours
    max_marks: int
    instructions: str
    sections: list[ExamPaperSection]
