"""
Data models for the QP Analyst app.

These models serve THREE purposes at once:
1. Define what Claude must return (passed into the API call as the expected schema)
2. Validate that response automatically (Pydantic raises if Claude returns garbage)
3. Define what gets stored in / read from the database

Keeping one schema for all three means there's no drift between "what we asked
Claude for" and "what we save to the DB" and "what the frontend receives."
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


ExamType = Literal["CIA-1", "CIA-2", "CIA-3", "End Semester", "Model Exam"]
QuestionType = Literal["Theory", "Numerical", "Diagram", "Derivation", "Programming"]


class ExtractedQuestion(BaseModel):
    """A single question, as classified by Claude."""
    question_number: str          # e.g. "1a", "2", "5(ii)"
    question_text: str
    unit: int = Field(ge=1, le=5)
    topic: str                    # e.g. "Normalization", "Tomasulo's Algorithm"
    marks: int
    question_type: QuestionType
    has_diagram: bool = False     # True if answering this question requires reading a
                                   # figure/graph/chart printed on the paper. Independent
                                   # of question_type — a "Numerical" question about a
                                   # graph (e.g. Dijkstra's shortest path) still has_diagram=True.


class PaperMetadata(BaseModel):
    """Metadata Claude extracts/infers about the paper itself."""
    subject_name: str
    exam_type: ExamType
    department: Optional[str] = None
    year: Optional[int] = None


class PaperExtractionResult(BaseModel):
    """
    The full shape of what we ask Claude to return in one call:
    paper-level metadata + every question on the paper.
    This is the exact JSON schema passed to the Claude API call.
    """
    metadata: PaperMetadata
    questions: list[ExtractedQuestion]
    transcribed_text: str  # full plain-text transcription of the paper, used later for scoped Q&A


class Paper(BaseModel):
    """Full DB record for a paper, returned to the frontend."""
    id: str
    filename: str
    subject_name: str
    exam_type: str
    department: Optional[str] = None
    year: Optional[int] = None
    uploaded_at: datetime
    question_count: int


class PaperSummary(BaseModel):
    """Aggregated analytics for one paper — powers the dashboard charts."""
    paper_id: str
    unit_distribution: dict[int, int]        # {1: 3, 2: 5, ...} -> question count per unit
    marks_by_unit: dict[int, int]            # {1: 16, 2: 25, ...} -> total marks per unit
    question_type_distribution: dict[str, int]
    total_marks: int
    total_questions: int


class AskRequest(BaseModel):
    question: str = Field(max_length=2000)


class AskResponse(BaseModel):
    answer: str
