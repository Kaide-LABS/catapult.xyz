import os
from dotenv import load_dotenv

load_dotenv()

# LLM Models
DRAFTING_MODEL = "gemini-3.1-pro-preview"      # Answer generation + citations
EXTRACTION_MODEL = "gemini-2.5-flash"           # Question extraction + domain tagging
EMBEDDING_MODEL = "text-embedding-004"          # Google embeddings

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# RAG Settings
CHUNK_SIZE = 512          # tokens
CHUNK_OVERLAP = 50        # tokens
TOP_K = 15                # retrieval candidates before reranking
RERANK_TOP_N = 3          # after FlashRank re-ranking
CHROMA_COLLECTION = "policy_knowledge_base"
CHROMA_PERSIST_DIR = "rag/knowledge_base/chroma_db"

# Confidence Thresholds
AUTO_APPROVE_THRESHOLD = 0.95
SME_REVIEW_THRESHOLD = 0.80

# Paths
POLICIES_DIR = "rag/knowledge_base/policies"
PAST_ANSWERS_DIR = "rag/knowledge_base/past_answers"