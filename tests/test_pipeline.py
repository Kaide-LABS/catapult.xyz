"""
Smoke test: run the full pipeline against a small sample questionnaire.
Requires GOOGLE_API_KEY set in .env and ChromaDB indexed (run indexer.py first).
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.graph import run_pipeline

def test_pipeline():
    result = run_pipeline(
        file_path="sample_questionnaires/test_sample.csv",
        file_name="test_sample.csv",
        file_type="csv"
    )

    assert len(result["questions"]) > 0, "No questions extracted"
    assert len(result["drafted_answers"]) > 0, "No answers drafted"
    assert len(result["approved_answers"]) > 0, "No answers routed"
    assert "export_path" in result, "No export generated"

    for qid, answer in result["approved_answers"].items():
        assert answer.status in ["AUTO_APPROVED", "PENDING_REVIEW"]
        assert len(answer.citations) > 0

    print(f"Pipeline complete: {len(result['questions'])} questions processed")
    print(f"Processing log:")
    for entry in result["processing_log"]:
        print(f"  {entry}")

if __name__ == "__main__":
    test_pipeline()
