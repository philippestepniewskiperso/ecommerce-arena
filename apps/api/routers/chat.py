"""Live chat: ticket creation, message history, WebSocket."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from apps.api.dependencies import get_db
from apps.api.models import Customer, StaffUser, SupportTicket, TicketMessage
from apps.api.auth import require_customer, get_session
from apps.api.events import emit_event, EventType
from apps.api.ws_manager import manager

router = APIRouter(tags=["chat"])


# ── REST ─────────────────────────────────────────────────────────────────────

@router.post("/api/customer/support/tickets")
async def create_ticket(
    payload: dict,
    customer: Customer = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Open a support ticket with an initial message."""
    subject = payload.get("subject", "Support request")
    body = payload.get("body", "")
    order_id = payload.get("order_id")

    result = await db.execute(func.count(SupportTicket.id))
    count = result.scalar() or 0
    number = f"TKT-{(count + 1):05d}"

    ticket = SupportTicket(
        number=number,
        customer_id=customer.id,
        order_id=uuid.UUID(order_id) if order_id else None,
        subject=subject,
        status="open",
        priority="medium",
    )
    db.add(ticket)
    await db.flush()

    if body:
        msg = TicketMessage(
            ticket_id=ticket.id,
            author_type="customer",
            author_id=customer.id,
            body=body,
            is_internal=False,
        )
        db.add(msg)
        await db.flush()

    await emit_event(
        db, EventType.TICKET_CREATED, "ticket", ticket.id,
        {"number": number, "subject": subject, "customer_id": str(customer.id)},
    )

    await db.commit()

    return {
        "id": str(ticket.id),
        "number": ticket.number,
        "subject": ticket.subject,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": ticket.created_at.isoformat(),
    }


@router.get("/api/customer/support/tickets")
async def list_customer_tickets(
    customer: Customer = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """List all tickets for the authenticated customer."""
    result = await db.execute(
        select(SupportTicket)
        .where(SupportTicket.customer_id == customer.id)
        .order_by(SupportTicket.created_at.desc())
    )
    tickets = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "number": t.number,
            "subject": t.subject,
            "status": t.status,
            "priority": t.priority,
            "created_at": t.created_at.isoformat(),
        }
        for t in tickets
    ]


@router.get("/api/customer/support/tickets/{ticket_id}/messages")
async def get_ticket_messages(
    ticket_id: uuid.UUID,
    customer: Customer = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Fetch message history for a ticket (customer must own it)."""
    result = await db.execute(
        select(SupportTicket).where(
            SupportTicket.id == ticket_id,
            SupportTicket.customer_id == customer.id,
        )
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    msgs = await db.execute(
        select(TicketMessage)
        .where(TicketMessage.ticket_id == ticket_id, TicketMessage.is_internal == False)  # noqa: E712
        .order_by(TicketMessage.created_at)
    )

    # Resolve display names for staff messages
    staff_cache: dict[str, str] = {}
    rows = []
    for m in msgs.scalars().all():
        if m.author_type == "staff":
            sid = str(m.author_id)
            if sid not in staff_cache:
                r = await db.execute(select(StaffUser).where(StaffUser.id == m.author_id))
                s = r.scalars().first()
                staff_cache[sid] = f"{s.first_name} {s.last_name}" if s else "Support"
            name = staff_cache[sid]
        else:
            name = f"{customer.first_name} {customer.last_name}"
        rows.append({
            "id": str(m.id),
            "sender_type": m.author_type,
            "sender_name": name,
            "body": m.body,
            "created_at": m.created_at.isoformat(),
        })

    return {
        "id": str(ticket.id),
        "number": ticket.number,
        "subject": ticket.subject,
        "status": ticket.status,
        "messages": rows,
    }


@router.get("/api/admin/support/tickets/{ticket_id}/messages")
async def get_ticket_messages_admin(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Fetch full message history for a ticket (staff, includes internal notes)."""
    result = await db.execute(
        select(SupportTicket).where(SupportTicket.id == ticket_id)
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    msgs = await db.execute(
        select(TicketMessage)
        .where(TicketMessage.ticket_id == ticket_id)
        .order_by(TicketMessage.created_at)
    )

    customer_result = await db.execute(
        select(Customer).where(Customer.id == ticket.customer_id)
    )
    customer = customer_result.scalars().first()
    customer_name = f"{customer.first_name} {customer.last_name}" if customer else "Customer"

    staff_cache: dict[str, str] = {}
    rows = []
    for m in msgs.scalars().all():
        if m.author_type == "staff":
            sid = str(m.author_id)
            if sid not in staff_cache:
                r = await db.execute(select(StaffUser).where(StaffUser.id == m.author_id))
                s = r.scalars().first()
                staff_cache[sid] = f"{s.first_name} {s.last_name}" if s else "Support"
            name = staff_cache[sid]
        else:
            name = customer_name
        rows.append({
            "id": str(m.id),
            "sender_type": m.author_type,
            "sender_name": name,
            "body": m.body,
            "internal": m.is_internal,
            "created_at": m.created_at.isoformat(),
        })

    return {
        "id": str(ticket.id),
        "number": ticket.number,
        "subject": ticket.subject,
        "status": ticket.status,
        "priority": ticket.priority,
        "customer_name": customer_name,
        "messages": rows,
    }


# ── WebSocket ─────────────────────────────────────────────────────────────────

@router.websocket("/ws/chat/{ticket_id}")
async def chat_ws(
    ticket_id: str,
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Bidirectional chat WebSocket. Auth via ?token= query param.
    Both customers and staff connect to the same endpoint.
    Incoming JSON: {"body": "message text"}
    Outgoing JSON: {"type": "message"|"joined"|"left", "author_type", "sender_name", "body", "created_at", ...}
    """
    # Validate token — works for both customer and staff sessions
    session = await get_session(db, token)
    if not session:
        await websocket.close(code=4001)
        return

    principal_type = session.principal_type
    principal_id = session.principal_id

    # Resolve display name
    if principal_type == "customer":
        r = await db.execute(select(Customer).where(Customer.id == principal_id))
        principal = r.scalars().first()
        display_name = f"{principal.first_name} {principal.last_name}" if principal else "Customer"
    else:
        r = await db.execute(select(StaffUser).where(StaffUser.id == principal_id))
        principal = r.scalars().first()
        display_name = f"{principal.first_name} {principal.last_name}" if principal else "Support"

    if not principal:
        await websocket.close(code=4001)
        return

    # Verify ticket exists (and customer owns it)
    try:
        ticket_uuid = uuid.UUID(ticket_id)
    except ValueError:
        await websocket.close(code=4004)
        return

    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_uuid))
    ticket = result.scalars().first()
    if not ticket:
        await websocket.close(code=4004)
        return

    if principal_type == "customer" and ticket.customer_id != principal_id:
        await websocket.close(code=4003)
        return

    await manager.connect(ticket_id, websocket, principal_type, display_name)

    # Notify room someone joined
    await manager.broadcast(ticket_id, {
        "type": "joined",
        "sender_type": principal_type,
        "sender_name": display_name,
        "ticket_id": ticket_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Mark ticket in_progress when staff joins
    if principal_type == "staff" and ticket.status == "open":
        ticket.status = "in_progress"
        await db.commit()

    try:
        while True:
            data = await websocket.receive_json()
            body = (data.get("body") or "").strip()
            if not body:
                continue

            # Persist message
            msg = TicketMessage(
                ticket_id=ticket_uuid,
                author_type=principal_type,
                author_id=principal_id,
                body=body,
                is_internal=False,
            )
            db.add(msg)
            await db.flush()
            await db.commit()

            payload = {
                "type": "message",
                "id": str(msg.id),
                "ticket_id": ticket_id,
                "sender_type": principal_type,
                "sender_name": display_name,
                "body": body,
                "created_at": msg.created_at.isoformat(),
            }
            await manager.broadcast(ticket_id, payload)

    except WebSocketDisconnect:
        manager.disconnect(ticket_id, websocket)
        await manager.broadcast(ticket_id, {
            "type": "left",
            "sender_type": principal_type,
            "sender_name": display_name,
            "ticket_id": ticket_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
