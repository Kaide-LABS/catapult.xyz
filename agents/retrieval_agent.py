from rag.retriever import retrieve
from models.schemas import QuestionPayload, RetrievalResult

def perform_retrieval(question: QuestionPayload) -> RetrievalResult:
    res = retrieve(query=question.normalized_text, question_id=question.id, domain_filter=question.domain)
    return res
