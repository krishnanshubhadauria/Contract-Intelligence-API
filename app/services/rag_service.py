import os
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.services.pdf_service import PDFService

class RAGService:
    def __init__(self):
        self.pdf_service = PDFService()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        chroma_dir = os.path.join(settings.data_dir, "chroma")
        os.makedirs(chroma_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="contracts",
            metadata={"hnsw:space": "cosine"}
        )
    
    def index_document(self, document_id: str, text: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Index a document by chunking and embedding"""
        metadata = self.pdf_service.get_metadata(document_id)
        pages = metadata.get("pages", [])
        page_offsets = metadata.get("page_offsets", [])
        
        # Chunk the text
        chunks = []
        chunk_ids = []
        chunk_metadatas = []
        
        for page_info in pages:
            page_text = page_info["text"]
            page_num = page_info["page"]
            page_start = page_info["char_start"]
            
            # Split page into chunks
            for i in range(0, len(page_text), chunk_size - chunk_overlap):
                chunk = page_text[i:i + chunk_size]
                if not chunk.strip():
                    continue
                
                chunk_start = page_start + i
                chunk_end = min(page_start + i + len(chunk), page_info["char_end"])
                
                chunk_id = f"{document_id}_page{page_num}_chunk{i}"
                chunks.append(chunk)
                chunk_ids.append(chunk_id)
                chunk_metadatas.append({
                    "document_id": document_id,
                    "page": page_num,
                    "char_start": chunk_start,
                    "char_end": chunk_end
                })
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks).tolist()
        
        # Store in ChromaDB
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=chunk_metadatas
        )
    
    def search(self, query: str, document_ids: List[str] = None, top_k: int = 5) -> List[Dict]:
        """Search for relevant chunks"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # Build where clause if document_ids specified
        where = None
        if document_ids:
            where = {"document_id": {"$in": document_ids}}
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )
        
        # Format results
        formatted_results = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
        
        return formatted_results
    
    def get_context_for_question(self, question: str, document_ids: List[str] = None, top_k: int = 5) -> Tuple[str, List[Dict]]:
        """Get relevant context chunks for a question"""
        results = self.search(question, document_ids, top_k)
        
        context_parts = []
        citations = []
        
        for result in results:
            metadata = result["metadata"]
            text = result["text"]
            context_parts.append(text)
            
            citations.append({
                "document_id": metadata["document_id"],
                "page": metadata.get("page"),
                "char_range": {
                    "start": metadata.get("char_start"),
                    "end": metadata.get("char_end")
                },
                "text": text[:200]  # Preview
            })
        
        context = "\n\n".join(context_parts)
        return context, citations

