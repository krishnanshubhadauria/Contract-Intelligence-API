from fastapi import APIRouter, HTTPException
from app.models.schemas import ExtractRequest, ExtractResponse, Party, Signatory
from app.services.pdf_service import PDFService
from app.services.llm_service import LLMService
from app.services.webhook_service import WebhookService
from app.core.metrics import extract_counter, request_duration
from fastapi import BackgroundTasks
import time

router = APIRouter()
pdf_service = PDFService()
llm_service = LLMService()
webhook_service = WebhookService()

@router.post("", response_model=ExtractResponse)
async def extract_fields(
    request: ExtractRequest,
    background_tasks: BackgroundTasks
):
    """
    Extract structured fields from a document.
    Returns parties, dates, terms, and other contract metadata.
    """
    start_time = time.time()
    
    try:
        # Get document metadata
        metadata = pdf_service.get_metadata(request.document_id)
        text = metadata.get("text", "")
        
        if not text:
            raise HTTPException(status_code=404, detail="Document text not found")
        
        # Extract fields using LLM
        extracted = await llm_service.extract_fields(text)
        
        # Format response
        parties = [Party(**p) if isinstance(p, dict) else Party(name=str(p)) for p in extracted.get("parties", [])]
        signatories = [Signatory(**s) if isinstance(s, dict) else Signatory(name=str(s)) for s in extracted.get("signatories", [])]
        
        response = ExtractResponse(
            document_id=request.document_id,
            parties=parties,
            effective_date=extracted.get("effective_date"),
            term=extracted.get("term"),
            governing_law=extracted.get("governing_law"),
            payment_terms=extracted.get("payment_terms"),
            termination=extracted.get("termination"),
            auto_renewal=extracted.get("auto_renewal"),
            confidentiality=extracted.get("confidentiality"),
            indemnity=extracted.get("indemnity"),
            liability_cap=extracted.get("liability_cap"),
            signatories=signatories
        )
        
        # Emit webhook
        background_tasks.add_task(
            webhook_service.emit_event,
            "extract_complete",
            request.document_id,
            "success",
            "Fields extracted successfully"
        )
        
        extract_counter.inc()
        request_duration.observe(time.time() - start_time)
        
        return response
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Document {request.document_id} not found")
    except Exception as e:
        background_tasks.add_task(
            webhook_service.emit_event,
            "extract_complete",
            request.document_id,
            "error",
            str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

