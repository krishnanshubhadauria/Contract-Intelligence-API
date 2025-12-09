from fastapi import APIRouter, HTTPException
from app.models.schemas import WebhookEvent
from pydantic import ValidationError

router = APIRouter()

@router.post("/events")
async def receive_webhook_event(event: WebhookEvent):
    """
    Receive webhook events (for testing/demo purposes).
    In production, this would be the endpoint that receives events from the system.
    """
    try:
        # In a real implementation, you might process/store the event here
        return {
            "status": "received",
            "event_type": event.event_type,
            "document_id": event.document_id,
            "timestamp": event.timestamp
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

