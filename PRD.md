# PRD: VSQ Compliance Engine Demo — "Trojan Horse" Pitch to Catapult

## Context
We're building a working demo to pitch our agentic AI services to Catapult (catapult.xyz), an enterprise AI workspace founded by ex-Palantir leaders. The strategy: demo the VSQ Compliance Engine (immediate, self-contained value) while visually showcasing the broader 3-module architecture to sell the Virtual FDE pipeline engagement.

---

# PRODUCT REQUIREMENTS DOCUMENT

## 1. Product Overview

### 1.1 Product Name
**Scatterbot Agentic Sidecar Suite** — VSQ Compliance Engine (Live Demo)

### 1.2 Elevator Pitch
A multi-agent AI system that autonomously ingests, answers, and routes enterprise vendor security questionnaires (SIG, CAIQ, NIST) with deterministic citation enforcement — reducing 40+ hour compliance cycles to under 60 minutes.

### 1.3 Strategic Framing (Trojan Horse)
- The Streamlit app opens on a **Module Hub** showing all 3 architectural concepts
- Only the VSQ module is live — the other 2 are marked "Architecture Ready"
- This visually pitches the full engagement before the demo even starts
- After the demo, the conversation naturally shifts to: "When do we start on the Data Sanitation Pipeline?"

### 1.4 Target Audience
- **Primary**: Catapult leadership (CEO: GTM/velocity focus, CTO: mathematical rigor focus)
- **Secondary**: Any enterprise AI startup drowning in security questionnaires

---

## 2. Architecture

### 2.1 Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | Streamlit | Fast prototyping, Python-native |
| Orchestration | LangGraph | Multi-agent state machine with deterministic routing |
| LLM (Drafting) | Gemini 3.1 Pro Preview (via Google AI API) | #1 on 12/18 frontier benchmarks, 94.3% GPQA, $2/$12 per 1M tokens |
| LLM (Extraction/Tagging) | Gemini 2.5 Flash (via Google AI API) | Cheapest structured output ($0.15/$0.60), native JSON schema enforcement |
| Embeddings | Google `text-embedding-004` | Unified under single GOOGLE_API_KEY, 2048 context (sufficient for 512-token chunks), 768 dims |
| Re-ranking | FlashRank (local) | Free, no API dependency, fast local cross-encoder |
| Vector Store | ChromaDB | Local, zero-infra |
| Document Parsing | Docling | Multi-format (PDF, XLSX, DOCX) |
| Data Validation | Pydantic v2 | Strict schema enforcement for all agent outputs |
| Export | openpyxl | Excel export of completed questionnaires |

### 2.1.1 LLM Selection Rationale

**API Providers: 1** (Google AI) + **1 local package** (FlashRank)

| Use Case | Model | Cost/1M Tokens | Why This Model |
|----------|-------|---------------|----------------|
| Answer Drafting + Citations | Gemini 3.1 Pro Preview | $2/$12 | Lowest hallucination among frontier models. #1 on 12/18 benchmarks. When CTO asks "what powers this?" — strongest answer. |
| Question Extraction | Gemini 2.5 Flash | $0.15/$0.60 | 3x cheaper than Gemini 3 Flash. Native JSON schema. Simple extraction doesn't need frontier reasoning. |
| Domain Auto-Tagging | Filename/header-based (deterministic) | Free | Policy docs have explicit domains. LLM tagging reserved for ambiguous sections only. |
| Embeddings | Google text-embedding-004 | $0.10/1M | Unified under single GOOGLE_API_KEY. 2048 context sufficient for 512-token chunks. 768 dims. |
| Re-ranking | FlashRank (local) | Free | No API provider needed. Local Python package. Production-viable cross-encoder. |

**Models explicitly rejected:**
- Claude Sonnet 4.6: 96.7% abstention rate is ideal but adds a 2nd API provider. Gemini 3.1 Pro compensates with superior overall benchmarks.
- Gemini 3 Flash: 3-5x more expensive than 2.5 Flash with no meaningful gain for structured extraction tasks.
- GPT-4o: 15.85% hallucination rate (FaithBench) — 2.4x worse than Gemini 2.5 Pro family.
- OpenAI text-embedding-3-large: Better context window (8K) but adds a 2nd API provider. 2K context is sufficient for our 512-token chunks.

### 2.2 Multi-Agent Architecture (LangGraph State Machine)

```
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                     │
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐           │
│  │  INTAKE   │───▶│ RETRIEVAL│───▶│ DRAFTING  │          │
│  │  AGENT    │    │  AGENT   │    │  AGENT    │          │
│  └──────────┘    └──────────┘    └──────────┘           │
│       │                               │                  │
│       │                               ▼                  │
│       │                         ┌──────────┐            │
│       │                         │ ROUTING   │            │
│       │                         │  AGENT    │            │
│       │                         └──────────┘            │
│       │                          │        │              │
│       │                    ≥0.95 │        │ <0.95        │
│       │                          ▼        ▼              │
│       │                    ┌────────┐ ┌────────┐        │
│       │                    │AUTO-   │ │SME     │        │
│       │                    │APPROVE │ │REVIEW  │        │
│       │                    └────────┘ └────────┘        │
│       │                          │        │              │
│       │                          ▼        ▼              │
│       │                    ┌─────────────────┐          │
│       │                    │   EXPORT AGENT   │          │
│       │                    └─────────────────┘          │
└─────────────────────────────────────────────────────────┘
```

### 2.3 Agent Specifications

#### Agent 1: Omnichannel Intake Agent
- **Input**: Raw file upload (PDF, XLSX, DOCX, CSV)
- **Process**:
  1. Docling parses the file into structured content
  2. Extract individual questions via regex + LLM hybrid extraction
  3. Normalize each question into a `QuestionPayload` Pydantic model
  4. Detect questionnaire framework (SIG, CAIQ, NIST, Custom) via header analysis
- **Output**: `List[QuestionPayload]` — normalized question queue
- **Pydantic Schema**:
```python
class QuestionPayload(BaseModel):
    id: str                          # Q-001, Q-002...
    original_text: str               # Raw question text
    normalized_text: str             # Cleaned/standardized
    domain: str                      # e.g., "Access Control", "Encryption"
    framework: str                   # SIG, CAIQ, NIST, Custom
    section: str | None              # Original section/category
    requires_evidence: bool          # Does the question ask for documentation?
```

#### Agent 2: Policy RAG Retrieval Agent
- **Input**: `QuestionPayload`
- **Process**:
  1. Generate embedding for `normalized_text`
  2. Query ChromaDB with `top_k=20`, applying metadata filters for `domain`
  3. Re-rank results using FlashRank cross-encoder scoring
  4. Return top 5 chunks with source metadata
- **Output**: `RetrievalResult` with ranked chunks + source citations
- **Pydantic Schema**:
```python
class PolicyChunk(BaseModel):
    content: str                     # The actual policy text
    source_document: str             # e.g., "SOC2_Type_II_Report_2025.pdf"
    section: str                     # e.g., "Section 4.2 - Access Controls"
    page: int | None                 # Page number if applicable
    relevance_score: float           # 0.0 - 1.0
    chunk_id: str                    # For traceability

class RetrievalResult(BaseModel):
    question_id: str
    chunks: list[PolicyChunk]        # Top 5 ranked chunks (from top_k=20 re-ranked)
    retrieval_confidence: float      # Aggregate confidence
```

#### Agent 3: Drafting & Citation Agent
- **Input**: `QuestionPayload` + `RetrievalResult`
- **Process**:
  1. System prompt enforces **strict citation rules**:
     - Every factual claim MUST reference a `[Source: document_name, Section X.X]` tag
     - If no retrieved chunk supports a claim, the agent MUST NOT generate it
     - Output MUST follow the `DraftedAnswer` schema (constrained via tool_use)
  2. Gemini 3.1 Pro generates answer using ONLY the retrieved chunks as context
  3. Confidence score is computed as: `min(retrieval_confidence, llm_self_assessed_confidence)`
- **Output**: `DraftedAnswer`
- **Citation Enforcement Logic** (CRITICAL):
```python
class Citation(BaseModel):
    source_document: str
    section: str
    chunk_id: str                    # Links back to exact chunk used
    quote: str                       # Verbatim excerpt from source

class DraftedAnswer(BaseModel):
    question_id: str
    answer_text: str                 # The generated response
    citations: list[Citation]        # MUST be non-empty
    confidence_score: float          # 0.0 - 1.0
    reasoning: str                   # Why this confidence level
    requires_sme_review: bool        # Auto-flagged if < 0.95

    @field_validator('citations')
    @classmethod
    def must_have_citations(cls, v):
        if len(v) == 0:
            raise ValueError('Answer must have at least one citation')
        return v

    @model_validator(mode='after')
    def enforce_sme_review_flag(self):
        if self.confidence_score < 0.95 and not self.requires_sme_review:
            raise ValueError('requires_sme_review must be True when confidence_score < 0.95')
        return self
```

- **Constrained Generation Prompt Pattern**:
```
You are a compliance answer drafter. You MUST:
1. ONLY use information from the provided policy chunks
2. NEVER generate information not present in the chunks
3. For EVERY factual statement, append [Source: {document}, {section}]
4. If chunks are insufficient to fully answer, set confidence < 0.80
5. Return your answer as structured JSON matching the DraftedAnswer schema exactly
```

#### Agent 4: SME Routing & Approval Agent
- **Input**: `DraftedAnswer`
- **Process**:
  1. If `confidence_score >= 0.95`: auto-approve, mark as `APPROVED`
  2. If `0.80 <= confidence_score < 0.95`: route to SME with draft pre-filled
  3. If `confidence_score < 0.80`: flag as `NEEDS_MANUAL_REVIEW`, highlight gaps
  4. In demo: SME review is simulated via an in-app approval UI
- **Output**: `ApprovedAnswer`
- **Pydantic Schema**:
```python
class ApprovedAnswer(BaseModel):
    question_id: str
    final_answer: str
    citations: list[Citation]
    status: Literal["AUTO_APPROVED", "SME_APPROVED", "PENDING_REVIEW"]
    confidence_score: float
    reviewer: str | None             # SME name if manually reviewed
    approval_timestamp: datetime
```

#### Agent 5: Export Agent
- **Input**: `List[ApprovedAnswer]` + original questionnaire format
- **Process**:
  1. Map answers back to original questionnaire structure
  2. Generate completed Excel/PDF with answers populated
  3. Create audit trail document with full citation lineage
- **Output**: Downloadable completed questionnaire + audit log

### 2.4 RAG Knowledge Base Structure

```
knowledge_base/
├── policies/                    # Source policy documents
│   ├── soc2_type_ii_report.md
│   ├── data_encryption_policy.md
│   ├── incident_response_plan.md
│   ├── access_control_policy.md
│   ├── gdpr_compliance_statement.md
│   ├── business_continuity_plan.md
│   └── penetration_test_summary.md
├── past_answers/                # Previously approved VSQ answers
│   ├── caiq_v4_completed_2025.json
│   └── sig_lite_completed_2025.json
└── chroma_db/                   # Vector store (auto-generated)
    └── ...
```

For the demo, we create **synthetic but realistic** policy documents that mirror what an AI startup like Catapult would actually have.

### 2.5 Embedding & Chunking Strategy
- **Chunking (two-pass)**:
  1. **Pass 1**: `MarkdownHeaderTextSplitter` — splits on `#`, `##`, `###` headers, preserving section hierarchy as metadata (header chain)
  2. **Pass 2**: `RecursiveCharacterTextSplitter` — only applied to sections exceeding 512 tokens (50 token overlap). Child chunks inherit parent section metadata.
- **Metadata per chunk**: `source_document`, `section` (full header chain, e.g., "SOC 2 > Security > Vulnerability Scanning"), `domain`
- **Domain tagging (deterministic + fallback)**:
  1. **Primary**: Filename-based mapping (e.g., `data_encryption_policy.md` → "Encryption", `access_control_policy.md` → "Access Control")
  2. **Fallback**: For documents spanning multiple domains (e.g., `soc2_type_ii_report.md`), tag at the top-level section header level using header text matching
  3. **LLM tagging**: Reserved only for ambiguous sections that don't match any rule — not called per-chunk

---

## 3. Frontend Specification (Streamlit)

### 3.1 Page Structure

```
app.py                           # Entry point → Module Hub
pages/
├── module_hub.py                # Landing page with 3 cards
├── vsq_engine/
│   ├── upload.py                # Step 1: Upload questionnaire
│   ├── processing.py            # Step 2: Watch agents work
│   ├── review.py                # Step 3: Review & approve answers
│   └── export.py                # Step 4: Download completed file
├── virtual_fde.py               # "Architecture Ready" placeholder
└── kinetic_dispatcher.py        # "Architecture Ready" placeholder
```

### 3.2 Module Hub Landing Page (CRITICAL — The Trojan Horse)

Layout: 3 cards in a row using `st.columns(3)`

**Card 1: Virtual FDE Data Sanitation Pipeline**
- Icon: Shield
- Status badge: `Architecture Ready` (blue/gray)
- Subtitle: "Pre-Ingestion Data Sanitation"
- Description: "Autonomous PII redaction, dynamic RBAC mapping, and vector lifecycle management. Ensures your RAG pipeline ingests only pristine, compliant data."
- Bottom: "View Architecture" (links to a static architecture diagram page)

**Card 2: Kinetic Action Dispatcher**
- Icon: Lightning
- Status badge: `Architecture Ready` (blue/gray)
- Subtitle: "Post-Generation Execution"
- Description: "Translates AI-generated insights into deterministic API calls across enterprise systems. HITL validation gates ensure safe kinetic execution."
- Bottom: "View Architecture" (links to a static architecture diagram page)

**Card 3: VSQ Compliance Engine**
- Icon: Checkmark
- Status badge: `Live Demo` (green, pulsing animation)
- Subtitle: "Automated Security Questionnaires"
- Description: "Multi-agent system that autonomously ingests, answers, and routes vendor security questionnaires with deterministic citation enforcement."
- Bottom: "Launch Demo" (navigates to the VSQ upload page)

**Header**: "Scatterbot Agentic Sidecar Suite" with tagline: "Enterprise deployment infrastructure for AI workspaces"

**Footer**: Small text: "Architected for Catapult by Scatterbot"

### 3.3 VSQ Engine — Upload Page
- File uploader accepting `.pdf`, `.xlsx`, `.docx`, `.csv`
- Framework auto-detection display (SIG / CAIQ / NIST / Custom)
- Preview of extracted questions in a data table
- "Begin Processing" button — navigates to processing page
- Sidebar: Knowledge base status (number of policies indexed, total chunks)

### 3.4 VSQ Engine — Processing Page (The "Wow" Moment)
- **Real-time agent activity feed** showing each agent working:
  - `[Intake Agent] Parsing document... extracted 247 questions`
  - `[Retrieval Agent] Processing Q-042: "Describe your encryption at rest..." — 3 policy matches found`
  - `[Drafting Agent] Generating answer for Q-042... confidence: 0.97`
  - `[Routing Agent] Q-042 auto-approved (0.97 >= 0.95)`
- **Progress bar** with question count: `142/247 questions processed`
- **Live statistics dashboard**:
  - Auto-approved: X (green)
  - Needs SME review: Y (amber)
  - Needs manual answer: Z (red)
  - Average confidence: X.XX
- **Streaming** — answers appear in real-time as agents complete them

### 3.5 VSQ Engine — Review Page
- Filterable table of all answers:
  - Filter by status: Auto-Approved / Needs Review / Manual
  - Filter by domain: Access Control, Encryption, etc.
  - Filter by confidence range
- Click any row to expand:
  - Original question
  - Generated answer with inline citation highlights
  - Source documents used (clickable to view the policy text)
  - Confidence score with reasoning
  - "Approve" / "Edit & Approve" / "Flag for SME" buttons
- Bulk approve for auto-approved answers

### 3.6 VSQ Engine — Export Page
- Download completed questionnaire (Excel format matching original)
- Download audit trail (JSON with full citation lineage)
- Summary statistics:
  - Total questions answered
  - Auto-approval rate
  - Average confidence
  - Time saved estimate (vs. manual baseline of 40+ hours)
- "Return to Module Hub" button

### 3.7 Architecture Ready Pages (Virtual FDE & Kinetic Dispatcher)
- Clean, professional architecture diagram (Mermaid or static image)
- Key bullet points of what the module does
- "Technical Specification Available" badge
- Subtle CTA: "Contact Scatterbot to discuss implementation"

---

## 4. Data Flow (End-to-End)

```
User uploads SIG questionnaire (Excel)
    |
    v
[Intake Agent] -> Docling parses -> regex + LLM extracts questions -> QuestionPayload[]
    |
    v
[For each QuestionPayload]:
    |
    |-> [Retrieval Agent] -> embed question -> ChromaDB top_k=5 -> re-rank -> RetrievalResult
    |
    |-> [Drafting Agent] -> constrained generation with citations -> DraftedAnswer
    |
    |-> [Routing Agent] -> confidence threshold check
    |       |
    |       |-- >= 0.95 -> AUTO_APPROVED
    |       |-- 0.80-0.95 -> SME_REVIEW (pre-filled draft)
    |       |-- < 0.80 -> MANUAL_REVIEW (flagged)
    |
    v
[Review UI] -> Human reviews/approves pending items
    |
    v
[Export Agent] -> Generate completed questionnaire + audit trail
```

---

## 5. Sample Policy Documents (Synthetic)

For the demo, we create 7 realistic policy documents covering the major compliance domains:

1. **SOC 2 Type II Report** — Covers security, availability, processing integrity, confidentiality, privacy
2. **Data Encryption Policy** — At-rest (AES-256), in-transit (TLS 1.3), key management
3. **Incident Response Plan** — Detection, triage, containment, communication, post-mortem
4. **Access Control Policy** — RBAC, MFA, least privilege, SSO, session management
5. **GDPR Compliance Statement** — Data subject rights, DPA, cross-border transfers, DPO
6. **Business Continuity Plan** — RTO/RPO, disaster recovery, failover, backup procedures
7. **Penetration Test Summary** — Scope, findings, remediation, third-party attestation

Each document should be 3-5 pages, written as if it belongs to a real AI SaaS company. This is critical for demo realism.

---

## 6. Project Structure

```
catapult.xyz/
├── CONTEXT.MD                       # Existing strategic context
├── PRD.md                           # This PRD
├── app.py                           # Streamlit entry point
├── requirements.txt                 # Python dependencies
├── .env.example                     # API key template
├── config.py                        # App configuration
├── agents/
│   ├── __init__.py
│   ├── graph.py                     # LangGraph workflow definition
│   ├── intake_agent.py              # Omnichannel Intake
│   ├── retrieval_agent.py           # Policy RAG Retrieval (top_k=20) + FlashRank re-ranking (top 5)
│   ├── drafting_agent.py            # Drafting & Citation (Gemini 3.1 Pro Preview)
│   ├── routing_agent.py             # SME Routing & Approval
│   └── export_agent.py              # Export Agent
├── models/
│   ├── __init__.py
│   └── schemas.py                   # All Pydantic models
├── rag/
│   ├── __init__.py
│   ├── indexer.py                   # Document chunking & embedding
│   ├── retriever.py                 # ChromaDB query + re-ranking
│   └── knowledge_base/
│       ├── policies/                # Synthetic policy docs (.md)
│       └── past_answers/            # Previously approved answers (.json)
├── ui/
│   ├── __init__.py
│   ├── module_hub.py                # Landing page
│   ├── vsq_upload.py                # Upload page
│   ├── vsq_processing.py           # Processing page
│   ├── vsq_review.py               # Review page
│   ├── vsq_export.py               # Export page
│   ├── architecture_fde.py          # Virtual FDE architecture page
│   ├── architecture_kinetic.py      # Kinetic Dispatcher architecture page
│   ├── components.py                # Shared UI components
│   └── styles.py                    # Custom CSS
├── tests/
│   ├── test_intake.py
│   ├── test_retrieval.py
│   ├── test_drafting.py
│   ├── test_routing.py
│   └── test_export.py
└── sample_questionnaires/
    ├── sig_lite_sample.xlsx          # Sample SIG Lite questionnaire
    └── caiq_v4_sample.xlsx           # Sample CAIQ v4 questionnaire
```

---

## 7. Dependencies

```
# Core
streamlit>=1.40.0
langgraph>=0.4.0
langchain>=0.3.0
langchain-google-genai>=2.0.0    # Gemini 3.1 Pro + 2.5 Flash + text-embedding-004
chromadb>=0.6.0
pydantic>=2.0.0

# Document Parsing
docling>=2.0.0
openpyxl>=3.1.0
python-docx>=1.0.0

# Re-ranking
flashrank>=0.2.0                  # Local cross-encoder reranker

# Utilities
python-dotenv>=1.0.0
tiktoken>=0.8.0
google-genai>=1.0.0               # Direct Gemini API access (embeddings + generation)
```

---

## 8. Acceptance Criteria

### Must Have (Demo Day)
- [ ] Module Hub landing page with 3 cards (2 architecture, 1 live)
- [ ] File upload supporting at least XLSX and PDF
- [ ] Intake agent extracts questions from uploaded questionnaire
- [ ] RAG retrieval against synthetic policy knowledge base
- [ ] Drafted answers with enforced citations (Pydantic validation)
- [ ] Confidence scoring with 3-tier routing (auto/SME/manual)
- [ ] Real-time processing feed showing agent activity
- [ ] Review page with filtering and inline citation display
- [ ] Export to Excel with answers populated
- [ ] Audit trail with full citation lineage
- [ ] Architecture pages for Virtual FDE and Kinetic Dispatcher

### Nice to Have
- [ ] Sample CAIQ v4 questionnaire pre-loaded for one-click demo
- [ ] Dark/professional theme matching enterprise aesthetic
- [ ] Processing time comparison vs. manual baseline
- [ ] Animated transitions between pages

---

## 9. Verification Plan

1. **Unit tests**: Each agent tested independently with mock inputs
2. **Integration test**: Full pipeline with sample SIG questionnaire
3. **Citation validation**: Verify every generated answer has >= 1 valid citation
4. **Confidence calibration**: Verify routing thresholds work correctly
5. **UI walkthrough**: Full demo flow from Module Hub -> Upload -> Process -> Review -> Export
6. **Edge cases**: Empty questionnaire, malformed Excel, questions with no policy match

---

## 10. Implementation Phases (For Gemini Execution)

### Phase 1: Foundation

**Goal**: Set up the project skeleton, all Pydantic schemas, synthetic policy documents, and the RAG indexing pipeline. After Phase 1, we should be able to run the indexer and query ChromaDB successfully.

**API Keys Required** (add to `.env`):
- `GOOGLE_API_KEY` — for Gemini 3.1 Pro + 2.5 Flash
- `OPENAI_API_KEY` — for text-embedding-3-large

#### Step 1: Project Setup
Create the following files:

**`requirements.txt`** — exact contents specified in Section 7 of this PRD.

**`.env.example`**:
```
GOOGLE_API_KEY=your_google_ai_api_key
```

**`config.py`**:
```python
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Models
DRAFTING_MODEL = "gemini-3.1-pro-preview"      # Answer generation + citations
EXTRACTION_MODEL = "gemini-2.5-flash"           # Question extraction + domain tagging
EMBEDDING_MODEL = "text-embedding-004"            # Google embeddings (768 dims)

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# RAG Settings
CHUNK_SIZE = 512          # tokens
CHUNK_OVERLAP = 50        # tokens
TOP_K = 20                # initial retrieval candidates (wide net)
RERANK_TOP_N = 5          # after FlashRank re-ranking
CHROMA_COLLECTION = "policy_knowledge_base"
CHROMA_PERSIST_DIR = "rag/knowledge_base/chroma_db"

# Confidence Thresholds
AUTO_APPROVE_THRESHOLD = 0.95
SME_REVIEW_THRESHOLD = 0.80

# Paths
POLICIES_DIR = "rag/knowledge_base/policies"
PAST_ANSWERS_DIR = "rag/knowledge_base/past_answers"
```

#### Step 2: Pydantic Schemas
Create **`models/__init__.py`** (empty) and **`models/schemas.py`** containing ALL Pydantic models defined in Section 2.3 of this PRD:
- `QuestionPayload`
- `PolicyChunk`
- `RetrievalResult`
- `Citation`
- `DraftedAnswer` (with `@field_validator` for citations)
- `ApprovedAnswer`

Additionally, add the LangGraph state model:
```python
from typing import TypedDict

class VSQState(TypedDict):
    """LangGraph state that flows through the entire workflow."""
    file_path: str                              # Path to temp file on disk (NOT raw bytes)
    file_name: str
    file_type: str                              # pdf, xlsx, docx, csv
    questions: list[QuestionPayload]
    retrieval_results: dict[str, RetrievalResult]  # question_id -> result
    drafted_answers: dict[str, DraftedAnswer]       # question_id -> draft
    approved_answers: dict[str, ApprovedAnswer]     # question_id -> approved
    processing_log: list[str]                       # real-time agent activity log
    framework_detected: str                         # SIG, CAIQ, NIST, Custom
```

#### Step 3: Synthetic Policy Documents
Create **`rag/knowledge_base/policies/`** directory with 7 markdown files. Each document should be 3-5 pages (roughly 1500-2500 words), written as if it belongs to a real AI SaaS company called "Acme AI" (neutral name for demo). The documents must contain specific, verifiable facts that the drafting agent can cite — not vague generalities.

**Files to create:**

1. **`soc2_type_ii_report.md`** — Structure with sections numbered (1.1, 1.2, etc.):
   - Security: firewall rules, IDS/IPS, vulnerability scanning cadence
   - Availability: 99.95% SLA, multi-region deployment (us-east-1, eu-west-1), auto-scaling
   - Processing integrity: input validation, checksums, reconciliation procedures
   - Confidentiality: data classification (Public, Internal, Confidential, Restricted), encryption at rest/transit
   - Privacy: data minimization, retention (90 days logs, 1 year audit), deletion procedures

2. **`data_encryption_policy.md`** — Specific algorithms and key lengths:
   - At-rest: AES-256-GCM via AWS KMS, customer-managed keys (CMK) optional
   - In-transit: TLS 1.3 mandatory, certificate pinning for mobile, HSTS headers
   - Key management: 90-day rotation, split-knowledge custodians, HSM-backed for prod
   - Database: column-level encryption for PII fields, envelope encryption pattern

3. **`incident_response_plan.md`** — Specific timelines and escalation:
   - Severity levels: P1 (15min response), P2 (1hr), P3 (4hr), P4 (24hr)
   - Detection: CloudTrail + GuardDuty + custom anomaly detection
   - Containment: automated isolation playbooks, network segmentation
   - Communication: customer notification within 72 hours (GDPR), board notification for P1
   - Post-mortem: blameless RCA within 5 business days, published to internal wiki

4. **`access_control_policy.md`** — Specific controls:
   - RBAC with 4 roles: Admin, Engineer, Analyst, Viewer
   - MFA mandatory: TOTP or hardware key (FIDO2/WebAuthn)
   - SSO via SAML 2.0 / OIDC, integrated with Okta
   - Session timeout: 30 min idle, 12 hour absolute
   - Least privilege: quarterly access reviews, JIT access for production
   - Audit logging: all access events to immutable log store, 1 year retention

5. **`gdpr_compliance_statement.md`** — Specific mechanisms:
   - DPO appointed: compliance@acme-ai.com
   - Data subject rights: automated portal for access/deletion/portability (30 day SLA)
   - Legal basis: legitimate interest for product analytics, consent for marketing
   - Cross-border: EU-US Data Privacy Framework, SCCs for non-adequate countries
   - Sub-processors: listed in Appendix A, 30-day notification for changes
   - DPIA: completed for core AI processing pipeline, reviewed annually

6. **`business_continuity_plan.md`** — Specific metrics:
   - RTO: 4 hours (critical systems), 24 hours (non-critical)
   - RPO: 1 hour (databases), 24 hours (file storage)
   - Backup: daily automated snapshots, cross-region replication, monthly restore tests
   - DR site: AWS eu-west-1 (primary: us-east-1), automated failover via Route 53
   - Testing: full DR exercise annually, tabletop exercises quarterly
   - Communication tree: CEO > CTO > VP Eng > SRE Lead, customer status page

7. **`penetration_test_summary.md`** — Specific findings:
   - Vendor: "SecureAudit Ltd" (annual engagement)
   - Scope: external perimeter, web app, API, mobile app
   - Last test: January 2026
   - Findings: 0 Critical, 1 High (remediated in 7 days), 3 Medium (remediated in 30 days), 5 Low
   - High finding: IDOR vulnerability in user profile API — fixed via server-side authz check
   - Methodology: OWASP Testing Guide v4.2, PTES
   - Re-test: confirmed all High/Medium findings remediated

#### Step 4: RAG Indexing Pipeline
Create **`rag/__init__.py`** (empty) and **`rag/indexer.py`**:

```python
"""
Document chunking and embedding pipeline.
Reads all .md files from policies/ directory, chunks them,
auto-tags domains via Gemini 2.5 Flash, embeds via OpenAI,
and stores in ChromaDB.
"""
```

The indexer must:
1. Read all `.md` files from `POLICIES_DIR`
2. **Pass 1 — Structural split**: Use `MarkdownHeaderTextSplitter` to split on `#`, `##`, `###` headers. Each chunk retains the full header chain as `section` metadata (e.g., "SOC 2 Type II Report > Security > Vulnerability Scanning").
3. **Pass 2 — Size split**: For any section chunk exceeding 512 tokens, apply `RecursiveCharacterTextSplitter` (512 tokens, 50 overlap). Child chunks inherit parent `section` metadata.
4. **Domain tagging (deterministic)**:
   - Map filenames to domains: `data_encryption_policy.md` → "Encryption", `access_control_policy.md` → "Access Control", etc.
   - For `soc2_type_ii_report.md` (multi-domain), tag by top-level section header text matching.
   - Only call Gemini 2.5 Flash for sections that don't match any rule (should be rare/zero for our synthetic docs).
5. Generate embeddings via Google `text-embedding-004` (768 dims)
6. Store in ChromaDB with metadata: `source_document`, `section` (full header chain), `domain`, `chunk_index`
7. Print summary: total docs processed, total chunks, chunks per domain

Create **`rag/retriever.py`**:
```python
"""
ChromaDB query + FlashRank re-ranking.
Takes a QuestionPayload, embeds the normalized_text,
queries ChromaDB top_k=5 with optional domain filter,
re-ranks via FlashRank, returns top 3 as RetrievalResult.
"""
```

The retriever must:
1. Embed the question via Google `text-embedding-004`
2. Query ChromaDB `top_k=20`, optionally filtering by `domain` metadata
3. Re-rank the 20 candidates using FlashRank cross-encoder
4. Return top 5 as a `RetrievalResult` with computed `retrieval_confidence` (average of top 5 relevance scores)

#### Step 5: Create Directory Structure
Ensure all directories exist:
```
rag/knowledge_base/policies/
rag/knowledge_base/past_answers/
rag/knowledge_base/chroma_db/
models/
agents/
ui/
tests/
sample_questionnaires/
```

Create empty `__init__.py` files in: `models/`, `agents/`, `rag/`, `ui/`.

#### Step 6: Verification
After Phase 1 is complete, run:
1. `pip install -r requirements.txt` — must succeed
2. `python rag/indexer.py` — must index all 7 policy docs, print chunk summary
3. `python -c "from rag.retriever import retrieve; print(retrieve('How do you encrypt data at rest?'))"` — must return relevant chunks from `data_encryption_policy.md`
4. `python -c "from models.schemas import DraftedAnswer; DraftedAnswer(question_id='test', answer_text='test', citations=[], confidence_score=0.5, reasoning='test', requires_sme_review=True)"` — must FAIL with validation error (empty citations)
5. `python -c "from models.schemas import DraftedAnswer, Citation; DraftedAnswer(question_id='test', answer_text='test', citations=[Citation(source_document='test.md', section='1.1', chunk_id='c1', quote='test')], confidence_score=0.8, reasoning='test', requires_sme_review=False)"` — must FAIL with validation error (confidence < 0.95 but requires_sme_review=False)

#### Acceptance Criteria (Phase 1)
- [ ] All directories and `__init__.py` files created
- [ ] `requirements.txt` with all dependencies
- [ ] `.env.example` with both API keys
- [ ] `config.py` with all settings and model names
- [ ] `models/schemas.py` with all 7 Pydantic models + `VSQState`
- [ ] 7 synthetic policy documents (1500-2500 words each, specific citable facts)
- [ ] `rag/indexer.py` — chunks, tags, embeds, stores in ChromaDB
- [ ] `rag/retriever.py` — queries ChromaDB, re-ranks via FlashRank, returns `RetrievalResult`
- [ ] All 4 verification commands pass

### Phase 2: Agent Core (Revised)

**Goal**: Implement all 5 LangGraph agents and wire them into a complete workflow graph using parallel processing (Map-Reduce) to meet enterprise performance expectations. After Phase 2, we should be able to programmatically run the full pipeline.

**Prerequisite**: Phase 1 complete. ChromaDB indexed with policy docs. All schemas in `models/schemas.py` available.

#### Step 1: LangGraph Workflow Definition

Create **`agents/graph.py`**:

```python
"""
LangGraph state machine defining the VSQ Compliance Engine workflow.
Nodes: intake → parallel retrieval & drafting (Map-Reduce) → routing → export
State: VSQState (defined in models/schemas.py)
"""
```

The graph must:
1. Import `VSQState` from `models/schemas.py`
2. Define a `StateGraph` with `VSQState`. Note that collections like `processing_log` must use `typing.Annotated` with reducers.
3. Add nodes: `intake`, `process_question` (a mapped node that runs retrieval, drafting, and routing per question in parallel), `export`
4. Wire edges to support `Send` API (Map-Reduce) for parallel question processing.
5. Compile the graph with `graph = workflow.compile()`

**Key design decisions:**
- Parallel processing using LangGraph Send API to process 100s of questions concurrently.
- State fields like `processing_log`, `drafted_answers`, and `approved_answers` use reducers to handle concurrent updates.

#### Step 2: Intake Agent

Create **`agents/intake_agent.py`**:

```python
"""
Omnichannel Intake Agent.
Parses uploaded files (PDF, XLSX, DOCX, CSV) deterministically.
Uses Gemini 2.5 Flash ONLY for domain tagging and cleaning, NOT for raw extraction from bulk text.
"""
```

The intake agent must:
1. **File parsing**: Use `openpyxl` or `pandas` to deterministically extract rows/questions for Excel/CSV.
2. **Domain tagging**: Call Gemini 2.5 Flash on the cleaned questions to assign the domain.
3. Return `Send` commands for each extracted question to trigger parallel processing.

#### Step 3: Retrieval Agent

Create **`agents/retrieval_agent.py`**:

Similar to before, but operates on a single `QuestionPayload` at a time (as part of the parallel map step), calling ChromaDB with `top_k=20`, then FlashRank.

#### Step 4: Drafting Agent

Create **`agents/drafting_agent.py`**:

The drafting agent must:
1. Implement a two-step Chain-of-Thought approach to enforce citations without hallucination.
2. First step: Prompt LLM to extract verbatim quotes from the retrieved chunks relevant to the question.
3. Second step: Draft the final answer based *only* on the extracted quotes.
4. Uses Gemini 3.1 Pro Preview with Pydantic structured output.

#### Step 5: Routing Agent

Create **`agents/routing_agent.py`**:

Operates on a single `DraftedAnswer`.
Applies confidence thresholds to determine status (`AUTO_APPROVED` or `PENDING_REVIEW`).

#### Step 6: Export Agent

Create **`agents/export_agent.py`**:

The export agent must:
1. Load the *original* uploaded Excel file via `openpyxl`.
2. Inject the answers into the exact cells/columns they belong to, preserving original formatting.
3. Append a new worksheet "Audit Trail" containing the citation lineage.
4. Save to a temporary file path.

#### Step 7: Wire It All Together

Update `agents/__init__.py` to expose the compiled graph.

#### Step 8: Verification
Same as original Phase 2, but testing parallel execution and original Excel format retention.

### Phase 3: Frontend

**Goal**: Build the complete Streamlit frontend — the Module Hub "Trojan Horse" landing page, the 4-step VSQ Engine flow (Upload → Processing → Review → Export), and the two "Architecture Ready" placeholder pages. After Phase 3, the full demo should be runnable end-to-end via `streamlit run app.py`.

**Prerequisite**: Phase 2 complete. `agents/graph.py` exposes `run_pipeline()`. All agent nodes functional. ChromaDB indexed.

#### Step 1: App Entry Point & Navigation

Create **`app.py`** (project root):

```python
"""
Streamlit entry point for the Scatterbot Agentic Sidecar Suite.
Uses st.session_state for navigation and pipeline state persistence.
"""
```

The entry point must:
1. Set page config: `st.set_page_config(page_title="Scatterbot Sidecar Suite", page_icon="🚀", layout="wide")`
2. Import and apply custom CSS from `ui/styles.py`
3. Implement a simple navigation system using `st.session_state["current_page"]` with these values:
   - `"module_hub"` (default)
   - `"vsq_upload"`
   - `"vsq_processing"`
   - `"vsq_review"`
   - `"vsq_export"`
   - `"arch_fde"`
   - `"arch_kinetic"`
4. Route to the appropriate page module based on `current_page`
5. **Do NOT use Streamlit's multi-page app (pages/ directory)** — use session state routing instead, so we have full control over navigation and state.

#### Step 2: Custom Styles

Create **`ui/styles.py`**:

```python
"""
Custom CSS for professional enterprise styling.
Returns a CSS string to be injected via st.markdown(css, unsafe_allow_html=True).
"""
```

Must include styles for:
1. **Module Hub cards**: bordered containers with hover shadow, consistent height (~300px), rounded corners
2. **Status badges**:
   - `.badge-live`: green background (#22c55e), white text, subtle pulse animation (`@keyframes pulse`)
   - `.badge-ready`: blue-gray background (#64748b), white text
3. **Processing feed**: monospace font, dark background (#1e1e2e), green text (#4ade80), scrollable container (max-height 400px)
4. **Confidence indicators**: color-coded spans — green (>=0.95), amber (0.80-0.95), red (<0.80)
5. **General**: Hide default Streamlit header/footer hamburger menu for cleaner demo look
6. **Font**: Use a clean sans-serif stack, slightly larger base font (16px)

Export a function `inject_styles()` that calls `st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)`.

#### Step 3: Shared UI Components

Create **`ui/components.py`**:

```python
"""
Reusable UI components shared across pages.
"""
```

Must include:
1. `render_header()` — renders the "Scatterbot Agentic Sidecar Suite" header with tagline "Enterprise deployment infrastructure for AI workspaces"
2. `render_footer()` — renders "Architected for Catapult by Scatterbot" in small muted text
3. `render_back_button(label: str, target_page: str)` — navigates back via session state
4. `render_confidence_badge(score: float) -> str` — returns HTML span with color-coded confidence value
5. `render_status_badge(status: str) -> str` — returns HTML for AUTO_APPROVED (green) / PENDING_REVIEW (amber)

#### Step 4: Module Hub Landing Page (CRITICAL — The Trojan Horse)

Create **`ui/module_hub.py`**:

```python
"""
Module Hub — the landing page that visually pitches all 3 modules.
Only VSQ Engine is live. Virtual FDE and Kinetic Dispatcher show 'Architecture Ready'.
This is the Trojan Horse: the demo starts by showing the full scope of what Scatterbot can build.
"""
```

The Module Hub must:
1. Call `render_header()`
2. Create `st.columns(3)` with three cards:

   **Card 1 — Virtual FDE Data Sanitation Pipeline:**
   - Use `st.container()` with custom HTML/CSS for the card styling
   - Icon: 🛡️
   - Status: `<span class="badge-ready">Architecture Ready</span>`
   - Subtitle: "Pre-Ingestion Data Sanitation"
   - Description: "Autonomous PII redaction, dynamic RBAC mapping, and vector lifecycle management. Ensures your RAG pipeline ingests only pristine, compliant data."
   - Button: "View Architecture →" — navigates to `arch_fde`

   **Card 2 — Kinetic Action Dispatcher:**
   - Icon: ⚡
   - Status: `<span class="badge-ready">Architecture Ready</span>`
   - Subtitle: "Post-Generation Execution"
   - Description: "Translates AI-generated insights into deterministic API calls across enterprise systems. HITL validation gates ensure safe kinetic execution."
   - Button: "View Architecture →" — navigates to `arch_kinetic`

   **Card 3 — VSQ Compliance Engine:**
   - Icon: ✅
   - Status: `<span class="badge-live">Live Demo</span>` (with CSS pulse animation)
   - Subtitle: "Automated Security Questionnaires"
   - Description: "Multi-agent system that autonomously ingests, answers, and routes vendor security questionnaires with deterministic citation enforcement."
   - Button: "Launch Demo →" — navigates to `vsq_upload`

3. Call `render_footer()`

**Visual priority**: The VSQ card should visually stand out — consider a slightly different border color (green) or elevated shadow compared to the other two cards.

#### Step 5: VSQ Upload Page

Create **`ui/vsq_upload.py`**:

```python
"""
VSQ Engine Step 1: Upload a security questionnaire.
Supports XLSX, CSV, PDF, DOCX.
Shows framework auto-detection and question preview before processing.
"""
```

The upload page must:
1. `render_header()` + breadcrumb: "Module Hub → VSQ Engine → Upload"
2. `render_back_button("← Back to Module Hub", "module_hub")`
3. **File uploader**: `st.file_uploader("Upload your questionnaire", type=["xlsx", "csv", "pdf", "docx"])`
4. On file upload:
   - Save to a temp file (use `tempfile.NamedTemporaryFile`)
   - Store `file_path`, `file_name`, `file_type` in `st.session_state`
   - Run the **intake agent only** (not full pipeline) to extract questions and detect framework
   - Display detected framework in a colored badge: `st.success(f"Framework detected: {framework}")`
   - Show extracted questions in `st.dataframe()` with columns: ID, Question, Domain, Section, Requires Evidence
   - Show count: `st.metric("Questions Extracted", len(questions))`
5. **Sidebar**: Knowledge base status panel:
   - Query ChromaDB for collection stats (number of documents, total chunks)
   - Display: "📚 Knowledge Base: 7 policies indexed, {N} chunks available"
6. **"Begin Processing" button**: Only enabled when questions are extracted. On click:
   - Store the extracted questions and framework in `st.session_state`
   - Navigate to `vsq_processing`

**Important**: The intake agent should run synchronously on upload so the user sees the preview immediately. The rest of the pipeline (retrieval → drafting → routing → export) runs on the processing page.

#### Step 6: VSQ Processing Page (The "Wow" Moment)

Create **`ui/vsq_processing.py`**:

```python
"""
VSQ Engine Step 2: Watch agents process questions in real-time.
Shows a live activity feed, progress bar, and statistics dashboard.
This is the 'wow' moment of the demo — the audience watches AI agents work.
"""
```

The processing page must:
1. `render_header()` + breadcrumb: "Module Hub → VSQ Engine → Processing"
2. Retrieve `questions`, `file_path`, `file_name`, `file_type`, `framework_detected` from `st.session_state`
3. **Layout**: Two columns — left (70%) for activity feed, right (30%) for live stats
4. **Left column — Activity Feed**:
   - Dark-themed container with monospace font (use the CSS class from styles.py)
   - Use `st.empty()` containers to stream log entries as they appear
   - Each log entry should appear with a slight visual distinction by agent:
     - `[Intake]` — blue
     - `[Retrieval]` — purple
     - `[Drafting]` — orange
     - `[Routing]` — green/amber depending on result
     - `[Export]` — white
5. **Progress bar**: `st.progress()` updated as each question completes: `{completed}/{total} questions processed`
6. **Right column — Live Statistics**:
   - Use `st.metric()` widgets that update as processing progresses:
     - "Auto-Approved" (green delta)
     - "Needs Review" (amber)
     - "Average Confidence" (formatted to 2 decimal places)
     - "Questions Processed"
7. **Pipeline execution approach**:
   - Since LangGraph `invoke()` is blocking, run the pipeline in a thread or use `st.status()` for progress indication
   - **Recommended approach**: Instead of calling `run_pipeline()` directly, call each agent step manually and update the UI between steps:
     ```python
     # Run intake (already done on upload page — reuse from session_state)
     # For each question, run retrieval → drafting → routing, updating UI after each
     # Finally run export
     ```
   - This gives granular control over the activity feed updates
   - Store intermediate results in `st.session_state` as they complete
8. **On completion**:
   - Show a success banner: `st.success("Processing complete! All {N} questions answered.")`
   - Auto-navigate or show button: "Review Answers →" — navigates to `vsq_review`

**Implementation note**: For the demo, processing 5 questions will take ~15-30 seconds (API latency). The real-time feed creates the impression of watching an intelligent system work — this is the emotional hook. Make the feed visually engaging.

#### Step 7: VSQ Review Page

Create **`ui/vsq_review.py`**:

```python
"""
VSQ Engine Step 3: Review and approve drafted answers.
Filterable table with expandable rows showing full answer details,
citations, and approval actions.
"""
```

The review page must:
1. `render_header()` + breadcrumb: "Module Hub → VSQ Engine → Review"
2. `render_back_button("← Back to Processing", "vsq_processing")`
3. Retrieve `approved_answers`, `drafted_answers`, `retrieval_results`, `questions` from `st.session_state`
4. **Filter bar** (horizontal row of filters):
   - Status filter: `st.selectbox` — "All", "Auto-Approved", "Pending Review"
   - Domain filter: `st.selectbox` — "All" + unique domains from questions
   - Confidence range: `st.slider` — range 0.0 to 1.0
5. **Summary metrics row**: 4 columns with `st.metric()`:
   - Total Questions
   - Auto-Approved (with green indicator)
   - Pending Review (with amber indicator)
   - Average Confidence
6. **Answer cards**: For each filtered answer, render an expandable card using `st.expander()`:
   - **Header line**: `Q-{id} | {domain} | {confidence_badge} | {status_badge}`
   - **Expanded content**:
     - **Original Question**: displayed in a quote block
     - **Generated Answer**: full answer text with inline `[Source: ...]` citations highlighted (use `st.markdown` with custom HTML to make citations visually distinct — e.g., light blue background)
     - **Citations table**: `st.dataframe()` with columns: Source Document, Section, Verbatim Quote
     - **Confidence reasoning**: italic text explaining the confidence score
     - **Action buttons** (in a row):
       - "✅ Approve" — sets status to `SME_APPROVED`, updates `st.session_state`
       - "✏️ Edit & Approve" — opens a `st.text_area` pre-filled with the answer for editing, then approves on submit
       - "🚩 Flag for SME" — sets a flag (visual indicator only for the demo)
7. **Bulk approve button**: "Approve All Auto-Approved" — batch-approves all answers with status `AUTO_APPROVED` → `SME_APPROVED`
8. **"Proceed to Export" button**: navigates to `vsq_export`

#### Step 8: VSQ Export Page

Create **`ui/vsq_export.py`**:

```python
"""
VSQ Engine Step 4: Download completed questionnaire and audit trail.
Shows summary statistics and provides download buttons.
"""
```

The export page must:
1. `render_header()` + breadcrumb: "Module Hub → VSQ Engine → Export"
2. `render_back_button("← Back to Review", "vsq_review")`
3. Retrieve `export_path`, `approved_answers`, `questions` from `st.session_state`
4. **Summary statistics** in a clean 4-column layout:
   - "Total Questions Answered": `st.metric()`
   - "Auto-Approval Rate": percentage with delta indicator
   - "Average Confidence": formatted to 2 decimal
   - "Estimated Time Saved": calculate as `len(questions) * 10 minutes` (baseline) displayed as hours vs. actual processing time. Show something like "~40 hours → 2 minutes"
5. **Download section**:
   - **Download Completed Questionnaire**: `st.download_button()` for the Excel file at `export_path`
   - **Download Audit Trail**: `st.download_button()` for a JSON file containing all citations with full lineage (generate this from `approved_answers` — serialize to JSON)
6. **Visual summary**: A simple bar chart or table showing answers by status (AUTO_APPROVED vs PENDING_REVIEW) and by domain
7. **"Return to Module Hub" button**: navigates back to `module_hub`

#### Step 9: Architecture Placeholder Pages

Create **`ui/architecture_fde.py`**:

```python
"""
Virtual FDE Data Sanitation Pipeline — Architecture Ready page.
Shows the architecture concept and positions it as a future engagement.
"""
```

Must include:
1. `render_header()` + `render_back_button("← Back to Module Hub", "module_hub")`
2. Title: "Virtual FDE Data Sanitation Pipeline"
3. Badge: `<span class="badge-ready">Architecture Ready</span>`
4. **Architecture diagram** using `st.markdown()` with a Mermaid diagram (Streamlit supports Mermaid via markdown code blocks):
   ```mermaid
   graph LR
       A[Raw Data Sources] --> B[PII Detection & Redaction]
       B --> C[Dynamic RBAC Mapping]
       C --> D[Vector Lifecycle Manager]
       D --> E[Clean RAG Pipeline]
   ```
5. **Key capabilities** (bullet list):
   - Autonomous PII detection across 40+ entity types (SSN, email, phone, credit card, etc.)
   - Context-aware redaction preserving semantic meaning for embeddings
   - Dynamic RBAC mapping — documents inherit access policies from source systems
   - Vector lifecycle management — automated re-indexing on policy changes
   - Compliance audit trail for every transformation
6. **Technical specification badge**: "📋 Full Technical Specification Available"
7. **CTA**: Muted text: "Contact Scatterbot to discuss implementation → scatterbot.ai"

Create **`ui/architecture_kinetic.py`**:

```python
"""
Kinetic Action Dispatcher — Architecture Ready page.
Shows the architecture concept for post-generation execution.
"""
```

Must include:
1. `render_header()` + `render_back_button("← Back to Module Hub", "module_hub")`
2. Title: "Kinetic Action Dispatcher"
3. Badge: `<span class="badge-ready">Architecture Ready</span>`
4. **Architecture diagram** (Mermaid):
   ```mermaid
   graph LR
       A[AI-Generated Insight] --> B[Intent Parser]
       B --> C[Action Planner]
       C --> D{HITL Gate}
       D -->|Approved| E[API Executor]
       D -->|Rejected| F[Feedback Loop]
       E --> G[Enterprise Systems]
   ```
5. **Key capabilities**:
   - Translates natural language AI outputs into deterministic API calls
   - Human-in-the-loop validation gates for irreversible actions
   - Pre-built connectors: Jira, Slack, Salesforce, GitHub, PagerDuty
   - Action rollback and audit logging
   - Rate limiting and circuit breaker patterns for safe execution
6. **Technical specification badge** and **CTA** (same pattern as FDE page)

#### Step 10: Verification

After Phase 3 is complete, run:
1. `streamlit run app.py` — must launch without errors
2. **Module Hub**: All 3 cards render, "Live Demo" badge pulses green, clicking "Launch Demo" navigates to upload
3. **Upload**: Upload `sample_questionnaires/test_sample.csv`, verify framework detection ("Custom") and 5 questions shown in preview table
4. **Processing**: Click "Begin Processing", verify real-time activity feed shows agent logs, progress bar advances, statistics update
5. **Review**: Verify all 5 answers displayed with expandable details, filters work, approve/edit buttons functional
6. **Export**: Download button produces an Excel file with answers and audit trail sheet
7. **Architecture pages**: Both render with Mermaid diagrams and capability lists

#### Acceptance Criteria (Phase 3)
- [ ] `app.py` — Streamlit entry point with session-state navigation
- [ ] `ui/styles.py` — Professional CSS with card styling, badges, feed styling, confidence colors
- [ ] `ui/components.py` — Shared header, footer, back button, badge renderers
- [ ] `ui/module_hub.py` — 3-card layout, VSQ card highlighted with "Live Demo" pulse
- [ ] `ui/vsq_upload.py` — File upload, framework detection, question preview, knowledge base sidebar
- [ ] `ui/vsq_processing.py` — Real-time activity feed, progress bar, live statistics
- [ ] `ui/vsq_review.py` — Filterable answers, expandable cards with citations, approve/edit/flag actions
- [ ] `ui/vsq_export.py` — Download buttons, summary statistics, time saved estimate
- [ ] `ui/architecture_fde.py` — Mermaid diagram, capability list, CTA
- [ ] `ui/architecture_kinetic.py` — Mermaid diagram, capability list, CTA
- [ ] Full demo flow works end-to-end: Module Hub → Upload → Process → Review → Export → Module Hub
- [ ] All navigation via session state (no Streamlit pages/ directory)

### Phase 4: Polish & Demo Prep
- Sample questionnaires (SIG, CAIQ)
- End-to-end testing
- UI polish, custom CSS
- Demo script / talking points
