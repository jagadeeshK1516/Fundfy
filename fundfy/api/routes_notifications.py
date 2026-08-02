"""Notification API routes with SSE streaming."""

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from fundfy.integrations.notifications import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

_notification_service = NotificationService()


@router.get("/stream")
async def notification_stream(request: Request):
    """SSE endpoint for real-time notifications."""
    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    async def event_generator():
        try:
            async for notification in _notification_service.subscribe(founder_id):
                if await request.is_disconnected():
                    break
                yield f"data: {json.dumps(notification)}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("")
async def list_notifications(request: Request, limit: int = 50):
    """List recent notifications."""
    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    notifications = await _notification_service.list_recent(founder_id, limit=limit)
    return {"notifications": notifications, "count": len(notifications)}


@router.patch("/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Mark a notification as read."""
    success = await _notification_service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"read": True}
