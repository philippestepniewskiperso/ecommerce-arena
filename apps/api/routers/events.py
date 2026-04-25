"""Event stream and webhook endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import asyncio

from apps.api.dependencies import get_db
from apps.api.models import DomainEvent, WebhookSubscription, WebhookDelivery
from apps.api.schemas import DomainEventResponse, WebhookSubscriptionCreate, WebhookSubscriptionResponse
from apps.api.auth import require_api_key, require_staff

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("/stream")
async def stream_events(
    db: AsyncSession = Depends(get_db),
):
    """Server-Sent Events stream of domain events (SSE)."""
    async def event_generator():
        last_id = 0
        while True:
            result = await db.execute(
                select(DomainEvent).where(DomainEvent.id > last_id).order_by(DomainEvent.created_at)
            )
            events = result.scalars().all()

            for event in events:
                last_id = max(last_id, event.id)
                payload = {
                    "id": str(event.id),
                    "type": event.type,
                    "aggregate_type": event.aggregate_type,
                    "aggregate_id": str(event.aggregate_id),
                    "payload": event.payload,
                    "created_at": event.created_at.isoformat(),
                }
                yield f"data: {json.dumps(payload)}\n\n"

            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/", response_model=list[DomainEventResponse])
async def list_events(
    event_type: str | None = None,
    aggregate_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List domain events (staff only)."""
    query = select(DomainEvent)
    if event_type:
        query = query.where(DomainEvent.type == event_type)
    if aggregate_type:
        query = query.where(DomainEvent.aggregate_type == aggregate_type)
    query = query.order_by(DomainEvent.created_at.desc()).limit(100)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/webhooks", response_model=WebhookSubscriptionResponse)
async def register_webhook(
    payload: WebhookSubscriptionCreate,
    api_key = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Register webhook subscription for agent (requires API key)."""
    import hashlib
    secret_hash = hashlib.sha256(payload.secret.encode()).hexdigest()

    subscription = WebhookSubscription(
        url=payload.url,
        events=payload.events,
        secret_hash=secret_hash,
        active=True,
    )
    db.add(subscription)
    await db.flush()
    await db.commit()
    return subscription


@router.get("/webhooks", response_model=list[WebhookSubscriptionResponse])
async def list_webhooks(
    api_key = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    """List webhook subscriptions (requires API key)."""
    result = await db.execute(select(WebhookSubscription).where(WebhookSubscription.active == True))
    return result.scalars().all()


@router.delete("/webhooks/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    subscription_id: str,
    api_key = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Delete webhook subscription (requires API key)."""
    result = await db.execute(select(WebhookSubscription).where(WebhookSubscription.id == subscription_id))
    subscription = result.scalars().first()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    subscription.active = False
    await db.flush()
    await db.commit()


@router.get("/webhooks/{subscription_id}/deliveries")
async def get_webhook_deliveries(
    subscription_id: str,
    api_key = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Get delivery history for webhook (requires API key)."""
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.subscription_id == subscription_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(50)
    )
    deliveries = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "status": d.status,
            "attempt_count": d.attempt_count,
            "response_status": d.response_status,
            "created_at": d.created_at.isoformat(),
            "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
        }
        for d in deliveries
    ]
