"""Notification service with Redis pub/sub and SSE support."""

import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

import asyncio

from sqlalchemy import select, update

from fundfy.db import async_session
from fundfy.models.notification import Notification
from fundfy.redis import get_redis


class NotificationService:
    """Handles publishing notifications and SSE streaming."""

    NOTIFICATION_TYPES = [
        "email_reply",
        "meeting_reminder",
        "grant_deadline",
        "job_complete",
        "document_ready",
    ]

    async def publish(
        self,
        founder_id: str,
        type: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> dict:
        """Publish a notification — stores in DB and broadcasts via Redis pub/sub."""
        notification_data = data or {}

        # Store in DB
        async with async_session() as session:
            notification = Notification(
                id=str(uuid.uuid4()),
                founder_id=founder_id,
                type=type,
                title=title,
                body=body,
                data=json.dumps(notification_data),
                read=False,
            )
            session.add(notification)
            await session.commit()
            await session.refresh(notification)
            notif_dict = self._to_dict(notification)

        # Broadcast via Redis pub/sub (best-effort)
        try:
            redis = get_redis()
            channel = f"notifications:{founder_id}"
            await redis.publish(channel, json.dumps(notif_dict))  # type: ignore
        except Exception:
            pass  # Redis may not be available

        return notif_dict

    async def subscribe(self, founder_id: str) -> AsyncGenerator[dict, None]:
        """Subscribe to notifications for a founder. Yields notification dicts."""
        redis = get_redis()
        channel = f"notifications:{founder_id}"

        # Try Redis pub/sub
        try:
            pubsub = redis.pubsub()  # type: ignore
            await pubsub.subscribe(channel)

            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    yield json.loads(message["data"])
                else:
                    await asyncio.sleep(0.5)
        except (AttributeError, Exception):
            # Fallback: poll DB for new notifications
            last_check = datetime.utcnow()
            while True:
                await asyncio.sleep(2)
                async with async_session() as session:
                    result = await session.execute(
                        select(Notification)
                        .where(
                            Notification.founder_id == founder_id,
                            Notification.created_at > last_check,
                        )
                        .order_by(Notification.created_at.asc())
                    )
                    notifications = result.scalars().all()
                    for notif in notifications:
                        yield self._to_dict(notif)
                    if notifications:
                        last_check = notifications[-1].created_at

    async def list_recent(self, founder_id: str, limit: int = 50) -> list[dict]:
        """List recent notifications for a founder."""
        async with async_session() as session:
            result = await session.execute(
                select(Notification)
                .where(Notification.founder_id == founder_id)
                .order_by(Notification.created_at.desc())
                .limit(limit)
            )
            notifications = result.scalars().all()
            return [self._to_dict(n) for n in notifications]

    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        async with async_session() as session:
            result = await session.execute(
                update(Notification)
                .where(Notification.id == notification_id)
                .values(read=True)
            )
            await session.commit()
            return result.rowcount > 0  # type: ignore

    def _to_dict(self, notification: Notification) -> dict:
        """Convert a Notification model to a dictionary."""
        return {
            "id": notification.id,
            "founder_id": notification.founder_id,
            "type": notification.type,
            "title": notification.title,
            "body": notification.body,
            "data": json.loads(notification.data) if notification.data else {},
            "read": notification.read,
            "created_at": notification.created_at.isoformat() if notification.created_at else None,
        }
