"""Domain event emission and webhook delivery."""
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any
import uuid
import httpx

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.models import DomainEvent, WebhookSubscription, WebhookDelivery


# Event types
class EventType:
    ORDER_PLACED = "order.placed"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_SHIPPED = "order.shipped"
    ORDER_DELIVERED = "order.delivered"
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"
    RETURN_REQUESTED = "return.requested"
    RETURN_APPROVED = "return.approved"
    STOCK_LOW = "stock.low"
    TICKET_CREATED = "ticket.created"
    TICKET_ESCALATED = "ticket.escalated"
    CUSTOMER_SIGNUP = "customer.signup"
    CAMPAIGN_SENT = "campaign.sent"
    SHIPMENT_CREATED = "shipment.created"
    SHIPMENT_DELIVERED = "shipment.delivered"


async def emit_event(
    db: AsyncSession,
    event_type: str,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
    payload: dict[str, Any],
) -> DomainEvent:
    """Emit domain event and trigger webhook delivery."""
    event = DomainEvent(
        type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.flush()

    # Queue webhook deliveries
    await queue_webhook_deliveries(db, event)

    return event


async def queue_webhook_deliveries(db: AsyncSession, event: DomainEvent) -> None:
    """Create webhook delivery tasks for matching subscriptions."""
    result = await db.execute(
        select(WebhookSubscription).where(
            WebhookSubscription.active == True,
        )
    )
    subscriptions = result.scalars().all()

    for subscription in subscriptions:
        if event.type not in subscription.events:
            continue

        delivery = WebhookDelivery(
            subscription_id=subscription.id,
            event_id=event.id,
            status="pending",
        )
        db.add(delivery)

    await db.flush()


async def deliver_webhooks(db: AsyncSession, batch_size: int = 10) -> None:
    """Deliver pending webhooks (background task)."""
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.status == "pending")
        .limit(batch_size)
    )
    deliveries = result.scalars().all()

    async with httpx.AsyncClient(timeout=10) as client:
        for delivery in deliveries:
            await _deliver_webhook(client, db, delivery)

    await db.commit()


async def _deliver_webhook(
    client: httpx.AsyncClient,
    db: AsyncSession,
    delivery: WebhookDelivery,
) -> None:
    """Deliver single webhook with retry logic."""
    # Fetch subscription and event
    result = await db.execute(
        select(WebhookSubscription).where(WebhookSubscription.id == delivery.subscription_id)
    )
    subscription = result.scalars().first()
    if not subscription:
        delivery.status = "failed"
        return

    result = await db.execute(select(DomainEvent).where(DomainEvent.id == delivery.event_id))
    event = result.scalars().first()
    if not event:
        delivery.status = "failed"
        return

    # Build payload
    payload = {
        "event_id": str(event.id),
        "type": event.type,
        "aggregate_type": event.aggregate_type,
        "aggregate_id": str(event.aggregate_id),
        "payload": event.payload,
        "created_at": event.created_at.isoformat(),
    }
    body_json = json.dumps(payload)

    # Sign with HMAC
    signature = hmac.new(
        subscription.secret_hash.encode(),
        body_json.encode(),
        hashlib.sha256,
    ).hexdigest()

    try:
        response = await client.post(
            subscription.url,
            json=payload,
            headers={
                "X-Webhook-Signature": f"sha256={signature}",
                "X-Event-Type": event.type,
                "X-Event-ID": str(event.id),
            },
        )

        delivery.attempt_count += 1
        delivery.response_status = response.status_code

        if response.status_code < 300:
            delivery.status = "success"
            delivery.delivered_at = datetime.now(timezone.utc)
            subscription.last_triggered_at = datetime.now(timezone.utc)
        elif delivery.attempt_count >= 3:
            delivery.status = "failed"
            delivery.response_body = response.text[:500]
        else:
            delivery.status = "pending"
            from datetime import timedelta
            delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=5 * delivery.attempt_count)

    except Exception as e:
        delivery.attempt_count += 1
        delivery.response_body = str(e)[:500]

        if delivery.attempt_count >= 3:
            delivery.status = "failed"
        else:
            delivery.status = "pending"
            from datetime import timedelta
            delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=5 * delivery.attempt_count)
