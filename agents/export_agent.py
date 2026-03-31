import shutil
import openpyxl
from openpyxl.styles import PatternFill
from models.schemas import VSQState

GREEN_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

def export_node(state: VSQState):
    original_path = state["file_path"]
    export_path = original_path.replace(".xlsx", "_completed.xlsx").replace(".csv", "_completed.xlsx")
    
    log = []
    
    if state["file_type"] == "xlsx":
        try:
            shutil.copy(original_path, export_path)
            wb = openpyxl.load_workbook(export_path)
            sheet = wb.active
            
            ans_col = sheet.max_column + 1
            sheet.cell(row=1, column=ans_col, value="Answer")
            sheet.cell(row=1, column=ans_col+1, value="Status")
            sheet.cell(row=1, column=ans_col+2, value="Confidence")
            sheet.cell(row=1, column=ans_col+3, value="Citations")

            ans_map = {}
            for q_id, approved in state.get("approved_answers", {}).items():
                q_text = ""
                for q in state.get("questions", []):
                    if q.id == q_id:
                        q_text = q.original_text
                        break
                if q_text:
                    ans_map[q_text] = approved

            for row in range(2, sheet.max_row + 1):
                for col in range(1, sheet.max_column):
                    cell_val = str(sheet.cell(row=row, column=col).value).strip()
                    if cell_val in ans_map:
                        approved = ans_map[cell_val]
                        sheet.cell(row=row, column=ans_col, value=approved.final_answer)
                        sheet.cell(row=row, column=ans_col+1, value=approved.status)
                        sheet.cell(row=row, column=ans_col+2, value=approved.confidence_score)
                        cites = "\n".join([f"{c.source_document} ({c.section})" for c in approved.citations])
                        sheet.cell(row=row, column=ans_col+3, value=cites)
                        fill = GREEN_FILL if approved.status == "AUTO_APPROVED" else YELLOW_FILL
                        for c_idx in range(ans_col, ans_col + 4):
                            sheet.cell(row=row, column=c_idx).fill = fill
                        break
            
            audit_ws = wb.create_sheet("Audit Trail")
            audit_ws.append(["Question ID", "Source Document", "Section", "Chunk ID", "Verbatim Quote", "Relevance Score"])
            for q_id, approved in state.get("approved_answers", {}).items():
                retrieval = state.get("retrieval_results", {}).get(q_id)
                chunk_scores = {}
                if retrieval:
                    chunk_scores = {ch.chunk_id: ch.relevance_score for ch in retrieval.chunks}
                for c in approved.citations:
                    score = chunk_scores.get(c.chunk_id, "N/A")
                    audit_ws.append([q_id, c.source_document, c.section, c.chunk_id, c.quote, score])
                    
            wb.save(export_path)
            log.append(f"[Export] Saved completed Excel to {export_path}")
        except Exception as e:
            log.append(f"[Export] Excel export failed: {str(e)}")
            export_path = ""
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Completed Questionnaire"
        ws.append(["Question ID", "Original Question", "Answer", "Status", "Confidence", "Citations"])

        for q_id, approved in state.get("approved_answers", {}).items():
            q_text = next((q.original_text for q in state.get("questions", []) if q.id == q_id), "")
            cites = "\n".join([f"{c.source_document} ({c.section})" for c in approved.citations])
            ws.append([q_id, q_text, approved.final_answer, approved.status, approved.confidence_score, cites])
            fill = GREEN_FILL if approved.status == "AUTO_APPROVED" else YELLOW_FILL
            for col_idx in range(1, 7):
                ws.cell(row=ws.max_row, column=col_idx).fill = fill

        audit_ws = wb.create_sheet("Audit Trail")
        audit_ws.append(["Question ID", "Source Document", "Section", "Chunk ID", "Verbatim Quote", "Relevance Score"])
        for q_id, approved in state.get("approved_answers", {}).items():
            retrieval = state.get("retrieval_results", {}).get(q_id)
            chunk_scores = {}
            if retrieval:
                chunk_scores = {ch.chunk_id: ch.relevance_score for ch in retrieval.chunks}
            for c in approved.citations:
                score = chunk_scores.get(c.chunk_id, "N/A")
                audit_ws.append([q_id, c.source_document, c.section, c.chunk_id, c.quote, score])

        wb.save(export_path)
        log.append(f"[Export] Saved completed Excel to {export_path}")
        
    total = len(state.get("approved_answers", {}))
    auto = sum(1 for a in state.get("approved_answers", {}).values() if a.status == "AUTO_APPROVED")
    review = total - auto
    log.append(f"[Export] {total} answers ({auto} auto-approved, {review} pending review)")

    return {"export_path": export_path, "processing_log": log}
