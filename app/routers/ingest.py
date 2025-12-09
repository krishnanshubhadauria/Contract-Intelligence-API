from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
from app.models.schemas import DocumentIngestResponse
from app.services.pdf_service import PDFService
from app.services.rag_service import RAGService
from app.services.webhook_service import WebhookService
from app.core.metrics import ingest_counter, request_duration
import time

router = APIRouter()
pdf_service = PDFService()
rag_service = RAGService()
webhook_service = WebhookService()

@router.post("", response_model=DocumentIngestResponse)
async def ingest_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    Ingest one or more PDF documents.
    Uploads PDFs, extracts text, stores metadata, and indexes for RAG.
    """
    start_time = time.time()
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    document_ids = []
    
    for file in files:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
        
        try:
            # Read file content
            content = await file.read()
            
            # Save PDF and get document_id
            document_id = await pdf_service.save_pdf(content, file.filename)
            
            # Extract text and metadata
            metadata = pdf_service.extract_text(document_id)
            
            # Index for RAG (in background)
            background_tasks.add_task(
                rag_service.index_document,
                document_id,
                metadata["text"]
            )
            
            # Emit webhook event (in background)
            background_tasks.add_task(
                webhook_service.emit_event,
                "ingest_complete",
                document_id,
                "success",
                f"Document {file.filename} ingested successfully"
            )
            
            document_ids.append(document_id)
            
        except Exception as e:
            # Emit error webhook
            background_tasks.add_task(
                webhook_service.emit_event,
                "ingest_complete",
                file.filename,
                "error",
                str(e)
            )
            raise HTTPException(status_code=500, detail=f"Error processing {file.filename}: {str(e)}")
    
    ingest_counter.inc(len(document_ids))
    request_duration.observe(time.time() - start_time)
    
    return DocumentIngestResponse(
        document_ids=document_ids,
        message=f"Successfully ingested {len(document_ids)} document(s)"
    )

