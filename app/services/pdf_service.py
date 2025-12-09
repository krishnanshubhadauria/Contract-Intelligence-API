import os
import uuid
import json
from typing import List, Dict, Tuple
import pdfplumber
import PyPDF2
from pathlib import Path
from app.core.config import settings

class PDFService:
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.data_dir = Path(settings.data_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
    
    async def save_pdf(self, file_content: bytes, filename: str) -> str:
        """Save PDF file and return document_id"""
        document_id = str(uuid.uuid4())
        file_path = self.upload_dir / f"{document_id}.pdf"
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return document_id
    
    def extract_text(self, document_id: str) -> Dict[str, any]:
        """Extract text from PDF with page information"""
        file_path = self.upload_dir / f"{document_id}.pdf"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document {document_id} not found")
        
        text_by_page = []
        full_text = ""
        char_offset = 0
        page_offsets = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text() or ""
                    text_by_page.append({
                        "page": page_num,
                        "text": page_text,
                        "char_start": char_offset,
                        "char_end": char_offset + len(page_text)
                    })
                    full_text += page_text + "\n"
                    page_offsets.append(char_offset)
                    char_offset += len(page_text) + 1
        except Exception as e:
            # Fallback to PyPDF2
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    text_by_page.append({
                        "page": page_num,
                        "text": page_text,
                        "char_start": char_offset,
                        "char_end": char_offset + len(page_text)
                    })
                    full_text += page_text + "\n"
                    page_offsets.append(char_offset)
                    char_offset += len(page_text) + 1
        
        metadata = {
            "document_id": document_id,
            "filename": file_path.name,
            "text": full_text,
            "pages": text_by_page,
            "page_offsets": page_offsets,
            "total_chars": len(full_text)
        }
        
        # Save metadata
        metadata_path = self.data_dir / f"{document_id}_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return metadata
    
    def get_metadata(self, document_id: str) -> Dict:
        """Get stored metadata for a document"""
        metadata_path = self.data_dir / f"{document_id}_metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata for {document_id} not found")
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_page_for_char_position(self, document_id: str, char_pos: int) -> int:
        """Get page number for a character position"""
        metadata = self.get_metadata(document_id)
        page_offsets = metadata.get("page_offsets", [])
        
        for i, offset in enumerate(page_offsets):
            if i + 1 < len(page_offsets) and char_pos >= offset and char_pos < page_offsets[i + 1]:
                return i + 1
            elif i + 1 == len(page_offsets) and char_pos >= offset:
                return i + 1
        
        return 1

