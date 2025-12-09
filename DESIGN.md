## ContractIntelligence Design (≤2 pages)

### Goals
- Local-first FastAPI service that ingests PDFs, extracts fields, answers questions (RAG), and audits clauses.
- Run via Docker/Compose; minimal external deps beyond OpenAI (optional).

### Architecture
- FastAPI app (`main.py`) with routers: ingest, extract, ask (+stream), audit, webhook, admin.
- Services:
  - `pdf_service`: save PDFs, extract text/pages, store metadata (json).
  - `rag_service`: chunk + embed (sentence-transformers), persist to Chroma.
  - `llm_service`: OpenAI for extraction, Q&A, audit; rule-based fallbacks if no API key.
  - `webhook_service`: optional async event emitter.
  - `metrics`: Prometheus counters/histograms.
- Data dirs: `uploads/` (PDFs), `data/` (metadata + Chroma).

### Data model (key artifacts)
- Metadata: `{document_id, filename, text, pages[{page,text,char_start,char_end}], page_offsets, total_chars}` stored per doc.
- RAG chunks: ids `doc_page_chunk`, embedding vectors, metadata `{document_id,page,char_start,char_end}` in Chroma.
- API schemas in `app/models/schemas.py` for ingest, extract, ask, audit, webhook.

### Chunking rationale
- Chunk size 1000 chars, overlap 200. Small enough for dense coverage; overlap keeps context continuity across clause boundaries; page-based starting offsets keep citation alignment.

### Fallback behavior
- No OPENAI_API_KEY: extraction/QA/audit fall back to light rule-based logic (basic heuristics, no external calls).
- RAG still works (local embeddings + Chroma); answers degrade gracefully to “LLM not configured” if needed.
- PDF extraction: try pdfplumber, fallback to PyPDF2.

### Security & privacy notes
- No data leaves the container unless OpenAI or webhook configured.
- Webhook URL is optional and off by default.
- CORS wide-open for demo; lock down in production.
- Uploaded files kept on disk; clear `uploads/` and `data/` for hygiene.
- No auth implemented (scope/time); add API keys/JWT and audit logging for prod.

### Operational considerations
- Health: `GET /healthz`; Metrics: `GET /metrics`.
- Streaming answers via SSE at `/ask/stream`.
- Compose mounts `uploads/` and `data/` for persistence.
- Timeouts: Dockerfile sets longer pip timeouts for slow networks.

### Trade-offs / shortcuts
- Minimal test coverage (add integration tests for ingest→ask→audit path).
- Simple rule-based fallbacks; not deeply robust.
- Basic risk rules; extend with domain-specific patterns and better span detection.
- No background queue; uses FastAPI background tasks (OK for small workloads).


