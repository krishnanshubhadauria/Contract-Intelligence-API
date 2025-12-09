from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from typing import List, Optional
import os
from dotenv import load_dotenv

from app.routers import ingest, extract, ask, audit, admin, webhook
from app.core.config import settings
from app.core.metrics import setup_metrics

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    setup_metrics()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="ContractIntelligence API",
    description="AI-powered contract analysis and intelligence system",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
app.include_router(extract.router, prefix="/extract", tags=["Extract"])
app.include_router(ask.router, prefix="/ask", tags=["Ask"])
app.include_router(audit.router, prefix="/audit", tags=["Audit"])
app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])
app.include_router(admin.router, tags=["Admin"])

@app.get("/")
async def root():
    return {
        "message": "ContractIntelligence API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

