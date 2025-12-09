import os
import httpx
import asyncio
from datetime import datetime
from typing import Optional
from app.models.schemas import WebhookEvent
from app.core.config import settings

class WebhookService:
    def __init__(self):
        self.webhook_url = settings.webhook_url or os.getenv("WEBHOOK_URL")
    
    async def emit_event(self, event_type: str, document_id: str, status: str, message: Optional[str] = None):
        """Emit a webhook event"""
        if not self.webhook_url:
            return  # No webhook configured
        
        event = WebhookEvent(
            event_type=event_type,
            document_id=document_id,
            status=status,
            message=message,
            timestamp=datetime.utcnow()
        )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=event.model_dump(),
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
        except Exception as e:
            print(f"Webhook error: {e}")

