"""
Document chunking and embedding pipeline.
Reads all .md files from policies/ directory, chunks them,
auto-tags domains via fallback mappings, embeds via Google GenAI,
and stores in ChromaDB.
"""
import os
import glob
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
import chromadb
import chromadb.utils.embedding_functions as embedding_functions

# Need to make sure paths resolve correctly from project root
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    POLICIES_DIR, CHROMA_PERSIST_DIR, CHROMA_COLLECTION, 
    EMBEDDING_MODEL, GOOGLE_API_KEY, CHUNK_SIZE, CHUNK_OVERLAP
)

# Domain mapping based on filename
DOMAIN_MAP = {
    "data_encryption_policy.md": "Encryption",
    "access_control_policy.md": "Access Control",
    "incident_response_plan.md": "Incident Response",
    "gdpr_compliance_statement.md": "Privacy & GDPR",
    "business_continuity_plan.md": "Business Continuity",
    "penetration_test_summary.md": "Vulnerability Management",
    "soc2_type_ii_report.md": "Audit & Compliance"
}

def get_domain(filename):
    if filename in DOMAIN_MAP:
        return DOMAIN_MAP[filename]
    return "General"

def run_indexer():
    print(f"Reading from {POLICIES_DIR}...")
    files = glob.glob(os.path.join(POLICIES_DIR, "*.md"))
    
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=GOOGLE_API_KEY,
        model_name="models/text-embedding-004"
    )

    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=google_ef
    )

    total_docs = len(files)
    total_chunks = 0
    domain_counts = {}

    for file_path in files:
        filename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        md_splits = markdown_splitter.split_text(content)
        chunks = text_splitter.split_documents(md_splits)

        for i, chunk in enumerate(chunks):
            # Create a combined section header
            headers = [chunk.metadata.get(f"Header {j}") for j in range(1, 4)]
            section = " > ".join([h for h in headers if h])
            if not section:
                section = "General"

            domain = get_domain(filename)

            meta = {
                "source_document": filename,
                "section": section,
                "domain": domain,
                "chunk_index": i
            }
            
            for key, val in meta.items():
                if val is None:
                    meta[key] = "Unknown"

            collection.add(
                documents=[chunk.page_content],
                metadatas=[meta],
                ids=[f"{filename}_chunk_{i}"]
            )
            total_chunks += 1
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    print(f"Total docs processed: {total_docs}")
    print(f"Total chunks: {total_chunks}")
    print("Chunks per domain:")
    for d, c in domain_counts.items():
        print(f"  {d}: {c}")

if __name__ == "__main__":
    run_indexer()