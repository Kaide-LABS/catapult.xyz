from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
from models.schemas import VSQState, QuestionPayload
from agents.intake_agent import intake_node
from agents.retrieval_agent import perform_retrieval
from agents.drafting_agent import perform_drafting
from agents.routing_agent import perform_routing
from agents.export_agent import export_node

class QuestionState(TypedDict):
    question: QuestionPayload

def dispatch_questions(state: VSQState):
    sends = []
    for q in state.get("questions", []):
        sends.append(Send("process_question", {"question": q}))
    return sends

def process_question_node(state: QuestionState):
    q = state["question"]
    
    retrieval_res = perform_retrieval(q)
    draft_res = perform_drafting(q, retrieval_res)
    approved_res = perform_routing(draft_res)
    
    log_msg = f"[Process] Q-{q.id}: confidence={approved_res.confidence_score:.2f}, status={approved_res.status}"
    
    return {
        "retrieval_results": {q.id: retrieval_res},
        "drafted_answers": {q.id: draft_res},
        "approved_answers": {q.id: approved_res},
        "processing_log": [log_msg]
    }

workflow = StateGraph(VSQState)

workflow.add_node("intake", intake_node)
workflow.add_node("process_question", process_question_node)
workflow.add_node("export", export_node)

workflow.add_edge(START, "intake")
workflow.add_conditional_edges("intake", dispatch_questions, ["process_question"])
workflow.add_edge("process_question", "export")
workflow.add_edge("export", END)

graph = workflow.compile()

def run_pipeline(file_path: str, file_name: str, file_type: str) -> VSQState:
    initial_state = {
        "file_path": file_path,
        "file_name": file_name,
        "file_type": file_type,
        "questions": [],
        "retrieval_results": {},
        "drafted_answers": {},
        "approved_answers": {},
        "processing_log": [],
        "framework_detected": "Unknown",
        "export_path": ""
    }
    return graph.invoke(initial_state)
