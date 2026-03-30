from pydantic import BaseModel, field_validator, model_validator
from typing import TypedDict, Literal
from datetime import datetime

class QuestionPayload(BaseModel):
    id: str
    original_text: str
    normalized_text: str
    domain: str
    framework: str
    section: str | None
    requires_evidence: bool

class PolicyChunk(BaseModel):
    content: str
    source_document: str
    section: str
    page: int | None
    relevance_score: float
    chunk_id: str

class RetrievalResult(BaseModel):
    question_id: str
    chunks: list[PolicyChunk]
    retrieval_confidence: float

class Citation(BaseModel):
    source_document: str
    section: str
    chunk_id: str
    quote: str

class DraftedAnswer(BaseModel):
    question_id: str
    answer_text: str
    citations: list[Citation]
    confidence_score: float
    reasoning: str
    requires_sme_review: bool

    @field_validator('citations')
    @classmethod
    def must_have_citations(cls, v):
        if len(v) == 0:
            raise ValueError('Answer must have at least one citation')
        return v

    @model_validator(mode='after')
    def check_sme_review_threshold(self):
        from config import AUTO_APPROVE_THRESHOLD
        if self.confidence_score < AUTO_APPROVE_THRESHOLD and not self.requires_sme_review:
            raise ValueError(f'requires_sme_review must be True if confidence_score < {AUTO_APPROVE_THRESHOLD}')
        return self

class ApprovedAnswer(BaseModel):
    question_id: str
    final_answer: str
    citations: list[Citation]
    status: Literal["AUTO_APPROVED", "SME_APPROVED", "PENDING_REVIEW"]
    confidence_score: float
    reviewer: str | None
    approval_timestamp: datetime

class VSQState(TypedDict):
    """LangGraph state that flows through the entire workflow."""
    file_path: str
    file_name: str
    file_type: str                              # pdf, xlsx, docx, csv
    questions: list[QuestionPayload]
    retrieval_results: dict[str, RetrievalResult]  # question_id -> result
    drafted_answers: dict[str, DraftedAnswer]       # question_id -> draft
    approved_answers: dict[str, ApprovedAnswer]     # question_id -> approved
    processing_log: list[str]                       # real-time agent activity log
    framework_detected: str                         # SIG, CAIQ, NIST, Custom