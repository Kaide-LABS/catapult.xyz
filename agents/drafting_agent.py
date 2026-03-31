import json
from google import genai
from config import GOOGLE_API_KEY, DRAFTING_MODEL
from models.schemas import QuestionPayload, RetrievalResult, DraftedAnswer, Citation

client = genai.Client(api_key=GOOGLE_API_KEY)

def perform_drafting(question: QuestionPayload, retrieval_result: RetrievalResult) -> DraftedAnswer:
    if not retrieval_result.chunks:
        return DraftedAnswer(
            question_id=question.id,
            answer_text="No relevant policies found to answer this question.",
            citations=[Citation(source_document="N/A", section="N/A", chunk_id="N/A", quote="N/A")],
            confidence_score=0.0,
            reasoning="No retrieval chunks available.",
            requires_sme_review=True
        )
        
    system_prompt = """You are a compliance answer drafter for an enterprise AI company called "Acme AI".
STRICT RULES:
1. ONLY use information from the provided policy chunks below.
2. NEVER generate information not present in the chunks.
3. For EVERY factual statement, append [Source: {document}, {section}].
4. If chunks are insufficient to fully answer the question, set confidence_score < 0.80.
5. Return your answer as structured JSON matching this exact schema:
{
  "extracted_quotes": [{"chunk_id": "...", "quote": "..."}],
  "answer_text": "Your answer with [Source: doc, section] inline citations",
  "citations": [{"source_document": "...", "section": "...", "chunk_id": "...", "quote": "verbatim excerpt"}],
  "confidence_score": 0.0,
  "reasoning": "Why this confidence level",
  "requires_sme_review": true
}
"""
    
    user_prompt = "POLICY CHUNKS:\n---\n"
    for chunk in retrieval_result.chunks:
        user_prompt += f"[Chunk {chunk.chunk_id}] Source: {chunk.source_document}, Section: {chunk.section}\n{chunk.content}\n---\n"
    user_prompt += f"\nQUESTION: {question.original_text}"

    try:
        response = client.models.generate_content(
            model=DRAFTING_MODEL,
            contents=[system_prompt, user_prompt],
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        data = json.loads(response.text)
        
        llm_conf = float(data.get("confidence_score", 0.0))
        final_conf = min(retrieval_result.retrieval_confidence, llm_conf)
        
        req_sme = data.get("requires_sme_review", True)
        from config import AUTO_APPROVE_THRESHOLD
        if final_conf < AUTO_APPROVE_THRESHOLD:
            req_sme = True
            
        citations = []
        for c in data.get("citations", []):
            citations.append(Citation(
                source_document=c.get("source_document", "Unknown"),
                section=c.get("section", "Unknown"),
                chunk_id=c.get("chunk_id", "Unknown"),
                quote=c.get("quote", "Unknown")
            ))
            
        if not citations:
            citations.append(Citation(source_document="N/A", section="N/A", chunk_id="N/A", quote="N/A"))
            
        return DraftedAnswer(
            question_id=question.id,
            answer_text=data.get("answer_text", "Failed to generate answer."),
            citations=citations,
            confidence_score=final_conf,
            reasoning=data.get("reasoning", ""),
            requires_sme_review=req_sme
        )

    except Exception as e:
        return DraftedAnswer(
            question_id=question.id,
            answer_text=f"Drafting failed: {str(e)}",
            citations=[Citation(source_document="Error", section="Error", chunk_id="Error", quote="Error")],
            confidence_score=0.0,
            reasoning=str(e),
            requires_sme_review=True
        )
