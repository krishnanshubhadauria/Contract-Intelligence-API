# ContractIntelligence API

A production-ready AI-powered contract analysis and intelligence system built with FastAPI. This system ingests PDF contracts, extracts structured fields, answers questions using RAG (Retrieval-Augmented Generation), and performs risk audits.

## Features

- **PDF Ingestion**: Upload and process multiple PDF contracts
- **Structured Extraction**: Extract parties, dates, terms, and other contract metadata
- **Question Answering (RAG)**: Ask questions about contracts with citations
- **Risk Auditing**: Detect risky clauses (auto-renewal, unlimited liability, etc.)
- **Streaming Responses**: Real-time token streaming for Q&A
- **Webhook Events**: Event notifications for long-running tasks
- **Metrics & Monitoring**: Prometheus metrics and health checks

## API Endpoints

### Ingest
- `POST /ingest` - Upload one or more PDF documents

### Extract
- `POST /extract` - Extract structured fields from a document

### Ask (RAG)
- `POST /ask` - Answer questions about uploaded contracts
- `GET /ask/stream` - Stream answer tokens (SSE)

### Audit
- `POST /audit` - Audit contract for risky clauses

### Webhook
- `POST /webhook/events` - Receive webhook events (for testing)

### Admin
- `GET /healthz` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - OpenAPI/Swagger documentation

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (optional, for LLM features)

### Quick Start

1. **Clone the repository** (or navigate to the project directory)

2. **Create a `.env` file**:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   WEBHOOK_URL=your_webhook_url_here  # Optional
   ```

3. **Build and run with Docker**:
   ```bash
   docker-compose up --build
   ```

4. **Access the API**:
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - Health Check: http://localhost:8000/healthz
    - Metrics: http://localhost:8000/metrics

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   export OPENAI_API_KEY=your_key_here
   ```

3. **Run the server**:
   ```bash
   uvicorn main:app --reload
   ```

## Sample Contract PDFs

For testing, you can use these publicly available contract PDFs:

1. **NDA Template** (Non-Disclosure Agreement)
   - Source: [LegalTemplates.net NDA](https://www.legaltemplates.net/form/non-disclosure-agreement/)
   - Alternative: Search for "NDA template PDF" on legal document sites

2. **MSA Template** (Master Service Agreement)
   - Source: [LegalTemplates.net MSA](https://www.legaltemplates.net/form/master-service-agreement/)
   - Alternative: Many legal template sites offer MSA templates

3. **Terms of Service Template**
   - Source: [TermsFeed ToS Generator](https://www.termsfeed.com/blog/sample-terms-of-service-template/)
   - Alternative: Most SaaS companies publish their ToS publicly

4. **Software License Agreement**
   - Source: [LegalTemplates.net Software License](https://www.legaltemplates.net/form/software-license-agreement/)
   - Alternative: Open source licenses (MIT, Apache) are publicly available

5. **Employment Agreement Template**
   - Source: [LegalTemplates.net Employment](https://www.legaltemplates.net/form/employment-agreement/)
   - Alternative: HR template sites often provide employment agreements

**Note**: Always ensure you have permission to use any contract PDFs. The above are suggestions for publicly available templates. For production use, use your own contracts or obtain proper licensing.

### Downloading Sample PDFs

You can download sample PDFs using:

```bash
# Example: Download a sample NDA (adjust URL as needed)
curl -o sample_nda.pdf <url_to_pdf>

# Or use wget
wget -O sample_nda.pdf <url_to_pdf>
```

## Usage Examples

### 1. Ingest Documents

```bash
curl -X POST "http://localhost:8000/ingest" \
  -F "files=@contract1.pdf" \
  -F "files=@contract2.pdf"
```

Response:
```json
{
  "document_ids": ["uuid1", "uuid2"],
  "message": "Successfully ingested 2 document(s)"
}
```

### 2. Extract Fields

```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "uuid1"}'
```

### 3. Ask Questions

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the termination clause?",
    "document_ids": ["uuid1"]
  }'
```

### 4. Audit Contract

```bash
curl -X POST "http://localhost:8000/audit" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "uuid1"}'
```

### 5. Stream Answers

```bash
curl "http://localhost:8000/ask/stream?question=What%20are%20the%20payment%20terms?"
```

## Architecture

- **FastAPI**: Web framework
- **PyPDF2/pdfplumber**: PDF text extraction
- **OpenAI GPT-4**: LLM for extraction and Q&A
- **ChromaDB**: Vector database for RAG
- **Sentence Transformers**: Embeddings for semantic search
- **Prometheus**: Metrics collection

## Configuration

Environment variables:
- `OPENAI_API_KEY`: Required for LLM features
- `WEBHOOK_URL`: Optional webhook endpoint for events
- `UPLOAD_DIR`: Directory for uploaded PDFs (default: `uploads`)
- `DATA_DIR`: Directory for metadata and vector DB (default: `data`)

## Project Structure

```
.
├── app/
│   ├── core/
│   │   ├── config.py       # Configuration
│   │   └── metrics.py      # Prometheus metrics
│   ├── models/
│   │   └── schemas.py      # Pydantic models
│   ├── routers/
│   │   ├── ingest.py       # PDF ingestion
│   │   ├── extract.py      # Field extraction
│   │   ├── ask.py          # Q&A endpoints
│   │   ├── audit.py        # Risk auditing
│   │   ├── webhook.py      # Webhook handling
│   │   └── admin.py        # Admin endpoints
│   └── services/
│       ├── pdf_service.py  # PDF processing
│       ├── llm_service.py  # LLM integration
│       ├── rag_service.py  # RAG implementation
│       └── webhook_service.py  # Webhook emitter
├── prompts/               # LLM prompts used (verbatim) + rationale
├── eval/                  # Q&A eval set, script, summary placeholder
├── tests/                 # Minimal health check test
├── DESIGN.md              # Design doc (≤2 pages)
├── main.py                 # FastAPI app
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
└── README.md              # This file
```

## Testing

Test the API using the Swagger UI at http://localhost:8000/docs or use curl/Postman.
Run minimal automated tests:
```bash
pytest -q
```

## Trade-offs & Notes
- No auth/CORS hardening (demo scope); lock down for prod.
- Background tasks use FastAPI background tasks, not a queue (OK for small loads).
- Rule-based fallbacks are basic; quality improves with OPENAI_API_KEY set.
- Risk audit rules are starter patterns; extend for domain coverage.

## License

This is a demonstration project for educational purposes.

