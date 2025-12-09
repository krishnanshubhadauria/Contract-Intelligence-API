from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import AuditRequest, AuditResponse, AuditFinding
from app.services.pdf_service import PDFService
from app.services.llm_service import LLMService
from app.services.webhook_service import WebhookService
from app.core.metrics import audit_counter, request_duration
import time

router = APIRouter()
pdf_service = PDFService()
llm_service = LLMService()
webhook_service = WebhookService()

@router.post("", response_model=AuditResponse)
async def audit_contract(
    request: AuditRequest,
    background_tasks: BackgroundTasks
):
    """
    Audit a contract for risky clauses.
    Detects issues like auto-renewal with short notice, unlimited liability, etc.
    """
    start_time = time.time()
    
    try:
        # Get document metadata
        metadata = pdf_service.get_metadata(request.document_id)
        text = metadata.get("text", "")
        
        if not text:
            raise HTTPException(status_code=404, detail="Document text not found")
        
        # First extract fields
        extracted_fields = await llm_service.extract_fields(text)
        
        # Run audit
        findings_data = await llm_service.audit_contract(text, extracted_fields)
        
        # Format findings and add page numbers
        findings = []
        for finding_data in findings_data:
            char_range = finding_data.get("char_range")
            page = None
            if char_range:
                start = char_range.get("start")
                if start is not None:
                    page = pdf_service.get_page_for_char_position(request.document_id, start)
            
            findings.append(AuditFinding(
                severity=finding_data.get("severity", "medium"),
                category=finding_data.get("category", "unknown"),
                description=finding_data.get("description", ""),
                evidence=finding_data.get("evidence", ""),
                char_range=char_range,
                page=page
            ))
        
        # Emit webhook
        background_tasks.add_task(
            webhook_service.emit_event,
            "audit_complete",
            request.document_id,
            "success",
            f"Audit completed with {len(findings)} findings"
        )
        
        audit_counter.inc()
        request_duration.observe(time.time() - start_time)
        
        return AuditResponse(
            document_id=request.document_id,
            findings=findings
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Document {request.document_id} not found")
    except Exception as e:
        background_tasks.add_task(
            webhook_service.emit_event,
            "audit_complete",
            request.document_id,
            "error",
            str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

