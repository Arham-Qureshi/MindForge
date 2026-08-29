from pydantic import BaseModel, Field
from typing import Literal
from app.schemas.pyq_paper_schema import BlueprintPayload, ExamPaper


class TopicFrequency(BaseModel):
    topic: str
    percentage: float = Field(ge=0.0, le=1.0)
    question_count: int


class PredictedQuestion(BaseModel):
    question: str
    bloom_level: Literal["Apply", "Analyze", "Evaluate"]
    expected_marks: int
    probability_score: float = Field(ge=0.0, le=1.0)


class PYQAnalysisPayload(BaseModel):
    topic_frequency: list[TopicFrequency]
    predicted_questions: list[PredictedQuestion]
    blueprint: BlueprintPayload | None = None  # type: ignore
    exam_paper: ExamPaper | None = None  # type: ignore
