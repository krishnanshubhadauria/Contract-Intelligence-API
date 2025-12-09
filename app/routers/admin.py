from fastapi import APIRouter
from fastapi.responses import Response
from app.core.metrics import get_metrics

router = APIRouter()

@router.get("/healthz")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "ContractIntelligence API"
    }

@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    """
    metrics_data = get_metrics()
    return Response(content=metrics_data, media_type="text/plain")

@router.get("/docs")
async def docs():
    """
    Redirect to OpenAPI docs (same as /docs endpoint provided by FastAPI).
    """
    return {
        "message": "OpenAPI documentation available at /docs",
        "swagger_ui": "/docs",
        "openapi_json": "/openapi.json"
    }

