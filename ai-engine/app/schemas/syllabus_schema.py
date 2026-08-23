from pydantic import BaseModel, Field
from typing import Literal


class Unit(BaseModel):
    unit_number: int
    title: str
    estimated_hours: int
    topics: list[str]
    cognitive_level: Literal["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]


class PriorityTopic(BaseModel):
    topic: str
    weightage: float = Field(ge=0.0, le=1.0)


class SyllabusPayload(BaseModel):
    course_title: str
    total_units: int
    learning_path: list[Unit]
    priority_topics: list[PriorityTopic]