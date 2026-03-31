"""
ChromaDB query + FlashRank re-ranking.
Takes a query string, embeds it, queries ChromaDB top_k=20,
re-ranks via FlashRank, returns top 5.
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from flashrank import Ranker, RerankRequest
from config import (
    CHROMA_PERSIST_DIR, CHROMA_COLLECTION, 
    GOOGLE_API_KEY, TOP_K, RERANK_TOP_N
)
from models.schemas import RetrievalResult, PolicyChunk

_ranker = None

def _get_ranker():
    global _ranker
    if _ranker is None:
        _ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="/tmp")
    return _ranker

def retrieve(query: str, question_id: str = "unknown", domain_filter: str = None) -> RetrievalResult:
    google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=GOOGLE_API_KEY,
        model_name="models/text-embedding-004"
    )

    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=google_ef
    )
    
    where_clause = {"domain": domain_filter} if domain_filter else None
    
    results = collection.query(
        query_texts=[query],
        n_results=TOP_K,
        where=where_clause
    )
    
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    ids = results['ids'][0]
    
    if not docs:
        return RetrievalResult(question_id=question_id, chunks=[], retrieval_confidence=0.0)

    ranker = _get_ranker()
    
    passages = []
    for i in range(len(docs)):
        passages.append({
            "id": ids[i],
            "text": docs[i],
            "meta": metas[i]
        })
        
    rerankrequest = RerankRequest(query=query, passages=passages)
    reranked = ranker.rerank(rerankrequest)
    
    top_chunks = []
    for rank in reranked[:RERANK_TOP_N]:
        score = rank['score']
        # Convert sigmoid score back roughly or use directly as confidence
        chunk = PolicyChunk(
            content=rank['text'],
            source_document=rank['meta']['source_document'],
            section=rank['meta']['section'],
            page=None,
            relevance_score=float(score),
            chunk_id=str(rank['id'])
        )
        top_chunks.append(chunk)
        
    avg_confidence = sum([c.relevance_score for c in top_chunks]) / len(top_chunks) if top_chunks else 0.0
    
    return RetrievalResult(
        question_id=question_id,
        chunks=top_chunks,
        retrieval_confidence=avg_confidence
    )

if __name__ == "__main__":
    res = retrieve('How do you encrypt data at rest?')
    print(res)