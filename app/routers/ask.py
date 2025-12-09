from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import AskRequest, AskResponse, Citation
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.pdf_service import PDFService
from app.core.metrics import ask_counter, request_duration
import time

router = APIRouter()
rag_service = RAGService()
llm_service = LLMService()
pdf_service = PDFService()

@router.post("", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Answer a question about the uploaded contracts using RAG.
    Returns answer with citations to source documents.
    """
    start_time = time.time()
    
    try:
        # Get relevant context using RAG
        context, citations_data = rag_service.get_context_for_question(
            request.question,
            request.document_ids
        )
        
        if not context:
            return AskResponse(
                answer="No relevant information found in the uploaded documents.",
                citations=[]
            )
        
        # Generate answer using LLM
        answer = await llm_service.answer_question(request.question, context)
        
        # Format citations
        citations = []
        for cit_data in citations_data:
            citations.append(Citation(
                document_id=cit_data["document_id"],
                page=cit_data.get("page"),
                char_range=cit_data.get("char_range"),
                text=cit_data.get("text", "")
            ))
        
        ask_counter.inc()
        request_duration.observe(time.time() - start_time)
        
        return AskResponse(
            answer=answer,
            citations=citations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stream")
async def ask_question_stream(question: str, document_ids: str = None):
    """
    Stream answer tokens for a question.
    document_ids should be comma-separated if multiple.
    """
    try:
        doc_ids = document_ids.split(",") if document_ids else None
        
        # Get relevant context
        context, _ = rag_service.get_context_for_question(question, doc_ids)
        
        if not context:
            async def empty_response():
                yield "data: " + "No relevant information found.\n\n"
            return StreamingResponse(empty_response(), media_type="text/event-stream")
        
        # Stream answer
        async def generate():
            async for token in llm_service.answer_question_stream(question, context):
                yield f"data: {token}\n\n"
        
        ask_counter.inc()
        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        async def error_response():
            yield f"data: Error: {str(e)}\n\n"
        return StreamingResponse(error_response(), media_type="text/event-stream")

