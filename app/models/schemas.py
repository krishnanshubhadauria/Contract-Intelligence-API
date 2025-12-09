from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentIngestResponse(BaseModel):
    document_ids: List[str]
    message: str

class Party(BaseModel):
    name: str
    role: Optional[str] = None

class Signatory(BaseModel):
    name: str
    title: Optional[str] = None

class ExtractRequest(BaseModel):
    document_id: str

class ExtractResponse(BaseModel):
    document_id: str
    parties: List[Party] = []
    effective_date: Optional[str] = None
    term: Optional[str] = None
    governing_law: Optional[str] = None
    payment_terms: Optional[str] = None
    termination: Optional[str] = None
    auto_renewal: Optional[bool] = None
    confidentiality: Optional[str] = None
    indemnity: Optional[str] = None
    liability_cap: Optional[Dict[str, Any]] = None  # {"amount": 1000000, "currency": "USD"}
    signatories: List[Signatory] = []

class AskRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None  # If None, search all documents

class Citation(BaseModel):
    document_id: str
    page: Optional[int] = None
    char_range: Optional[Dict[str, int]] = None  # {"start": 0, "end": 100}
    text: str

class AskResponse(BaseModel):
    answer: str
    citations: List[Citation] = []

class AuditFinding(BaseModel):
    severity: str  # "high", "medium", "low"
    category: str  # e.g., "auto_renewal", "liability", "indemnity"
    description: str
    evidence: str
    char_range: Optional[Dict[str, int]] = None
    page: Optional[int] = None

class AuditRequest(BaseModel):
    document_id: str

class AuditResponse(BaseModel):
    document_id: str
    findings: List[AuditFinding] = []

class WebhookEvent(BaseModel):
    event_type: str  # "ingest_complete", "extract_complete", "audit_complete"
    document_id: str
    status: str  # "success", "error"
    message: Optional[str] = None
    timestamp: datetime

