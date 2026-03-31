from pydantic import BaseModel, field_validator, model_validator
from typing import TypedDict, Literal, Annotated
from datetime import datetime
import operator

def update_dict(old_dict: dict, new_dict: dict) -> dict:
    if old_dict is None:
        return new_dict
    old_dict.update(new_dict)
    return old_dict

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
    questions: Annotated[list[QuestionPayload], operator.add]
    retrieval_results: Annotated[dict[str, RetrievalResult], update_dict]
    drafted_answers: Annotated[dict[str, DraftedAnswer], update_dict]
    approved_answers: Annotated[dict[str, ApprovedAnswer], update_dict]
    processing_log: Annotated[list[str], operator.add]
    framework_detected: str                         # SIG, CAIQ, NIST, Custom
    export_path: str