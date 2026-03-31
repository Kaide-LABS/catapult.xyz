import os
import re
import json
import pandas as pd
from google import genai
from config import GOOGLE_API_KEY, EXTRACTION_MODEL
from models.schemas import QuestionPayload, VSQState

client = genai.Client(api_key=GOOGLE_API_KEY)

def detect_framework(file_name: str, sample_text: str) -> str:
    lower_text = (file_name + " " + sample_text).lower()
    if "sig" in lower_text or "standardized information gathering" in lower_text:
        return "SIG"
    if "caiq" in lower_text or "consensus assessments" in lower_text:
        return "CAIQ"
    if "nist" in lower_text or "800-53" in lower_text:
        return "NIST"
    return "Custom"

def extract_questions_deterministic(file_path: str, file_type: str) -> list[dict]:
    questions = []
    if file_type == "csv":
        df = pd.read_csv(file_path)
    elif file_type == "xlsx":
        df = pd.read_excel(file_path)
    else:
        # Fallback for pdf/docx if needed, but we focus on Excel/CSV for now.
        return []

    # Heuristic: Find columns with 'Question', 'Control', or 'Requirement'
    question_col = None
    id_col = None
    section_col = None

    for col in df.columns:
        col_lower = str(col).lower()
        if "question" in col_lower or "control" in col_lower or "requirement" in col_lower:
            question_col = col
        if "id" in col_lower or "identifier" in col_lower:
            id_col = col
        if "section" in col_lower or "domain" in col_lower or "category" in col_lower:
            section_col = col

    if not question_col:
        # Fallback: Just take the first string column that has long enough text
        for col in df.columns:
            if df[col].dtype == object and df[col].str.len().mean() > 20:
                question_col = col
                break

    if not question_col:
        return []

    for idx, row in df.iterrows():
        q_text = str(row[question_col]).strip()
        if not q_text or q_text == "nan" or len(q_text) < 10:
            continue
        
        q_id = str(row[id_col]) if id_col and pd.notna(row[id_col]) else f"Q-{idx+1:03d}"
        q_section = str(row[section_col]) if section_col and pd.notna(row[section_col]) else "General"
        
        questions.append({
            "id": q_id,
            "original_text": q_text,
            "section": q_section
        })
        
    return questions

def intake_node(state: VSQState):
    file_path = state["file_path"]
    file_name = state["file_name"]
    file_type = state["file_type"]

    log = [f"[Intake] Parsed {file_name} ({file_type})"]
    
    raw_questions = extract_questions_deterministic(file_path, file_type)
    framework = detect_framework(file_name, str(raw_questions[:2]))

    log.append(f"[Intake] Extracted {len(raw_questions)} questions deterministically.")
    log.append(f"[Intake] Detected framework: {framework}")

    # Process domains in batches using Gemini 2.5 Flash
    questions = []
    
    if raw_questions:
        prompt = "Classify the following security questionnaire questions into exactly ONE of these domains: Access Control, Encryption, Incident Response, Privacy & GDPR, Business Continuity, Vulnerability Management, Audit & Compliance, General.\n\n"
        prompt += "Return a JSON object where keys are question IDs and values are the domain name.\n\n"
        
        q_map = {q["id"]: q["original_text"] for q in raw_questions}
        prompt += json.dumps(q_map, indent=2)

        try:
            response = client.models.generate_content(
                model=EXTRACTION_MODEL,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            domain_map = json.loads(response.text)
        except Exception as e:
            log.append(f"[Intake] LLM tagging failed, using 'General' for all. Error: {str(e)}")
            domain_map = {}

        for rq in raw_questions:
            domain = domain_map.get(rq["id"], "General")
            
            # Simple heuristic for requires_evidence
            lower_q = rq["original_text"].lower()
            requires_evidence = any(kw in lower_q for kw in ["attach", "provide evidence", "upload", "certificate", "report"])

            payload = QuestionPayload(
                id=rq["id"],
                original_text=rq["original_text"],
                normalized_text=rq["original_text"], # Could apply further cleaning if needed
                domain=domain,
                framework=framework,
                section=rq["section"],
                requires_evidence=requires_evidence
            )
            questions.append(payload)

    return {
        "questions": questions,
        "framework_detected": framework,
        "processing_log": log
    }
