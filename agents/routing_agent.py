from datetime import datetime
from config import AUTO_APPROVE_THRESHOLD, SME_REVIEW_THRESHOLD
from models.schemas import DraftedAnswer, ApprovedAnswer

def perform_routing(draft: DraftedAnswer) -> ApprovedAnswer:
    if draft.confidence_score >= AUTO_APPROVE_THRESHOLD:
        status = "AUTO_APPROVED"
    elif draft.confidence_score >= SME_REVIEW_THRESHOLD:
        status = "PENDING_REVIEW"
    else:
        status = "PENDING_REVIEW"
        
    return ApprovedAnswer(
        question_id=draft.question_id,
        final_answer=draft.answer_text,
        citations=draft.citations,
        status=status,
        confidence_score=draft.confidence_score,
        reviewer=None,
        approval_timestamp=datetime.now()
    )
