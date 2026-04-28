"""Admin endpoints: CRUD operations for all resources with RBAC."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from apps.api.dependencies import get_db
from apps.api.models import (
    Product, Category, StaffUser, Order, Payment, Shipment,
    SupportTicket, Campaign, Page, Banner, Role, Permission, ApiKey,
    Customer,
)
from apps.api.schemas import (
    ProductResponse, ProductCreate, ProductUpdate, CategoryResponse,
    OrderResponse, PaymentResponse, ShipmentResponse, SupportTicketResponse,
    CampaignResponse, CampaignCreate, PageResponse, PageCreate,
    BannerResponse, RoleResponse, PermissionResponse, ApiKeyResponse, ApiKeyCreateResponse,
    SessionResponse,
)
from apps.api.auth import require_staff, generate_api_key, hash_api_key
from apps.api.auth.password import verify_password
from apps.api.auth.session import create_session
from apps.api.events import emit_event, EventType
from apps.api.models import TrackingEvent
from apps.api.mocks.carrier import create_label, advance_tracking, CARRIERS
from pydantic import BaseModel
import random
from datetime import datetime, timezone

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ============================================================================
# AUTH
# ============================================================================

class StaffLogin(BaseModel):
    email: str
    password: str


@router.post("/auth/login", response_model=SessionResponse)
async def staff_login(payload: StaffLogin, db: AsyncSession = Depends(get_db)):
    """Staff login — returns session token."""
    result = await db.execute(select(StaffUser).where(StaffUser.email == payload.email))
    staff = result.scalars().first()
    if not staff or not verify_password(payload.password, staff.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if staff.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")

    token, session = await create_session(db, "staff", staff.id, ttl_hours=8)
    await db.commit()
    return {"token": token, "expires_at": session.expires_at}


@router.get("/auth/me")
async def staff_me(staff: StaffUser = Depends(require_staff)):
    """Return current staff user info."""
    return {
        "id": str(staff.id),
        "email": staff.email,
        "first_name": staff.first_name,
        "last_name": staff.last_name,
        "status": staff.status,
    }


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard")
async def dashboard(staff: StaffUser = Depends(require_staff), db: AsyncSession = Depends(get_db)):
    """KPI tiles for the dashboard."""
    total_orders = (await db.execute(select(func.count()).select_from(Order))).scalar()
    revenue = (await db.execute(
        select(func.sum(Order.total)).where(Order.status.in_(["delivered", "shipped", "confirmed"]))
    )).scalar() or 0
    open_tickets = (await db.execute(
        select(func.count()).select_from(SupportTicket).where(SupportTicket.status.in_(["open", "in_progress"]))
    )).scalar()
    total_customers = (await db.execute(select(func.count()).select_from(Customer))).scalar()
    pending_orders = (await db.execute(
        select(func.count()).select_from(Order).where(Order.status == "pending")
    )).scalar()
    urgent_tickets = (await db.execute(
        select(func.count()).select_from(SupportTicket).where(
            SupportTicket.priority == "urgent",
            SupportTicket.status.in_(["open", "in_progress"]),
        )
    )).scalar()

    return {
        "total_orders": total_orders,
        "revenue": float(revenue),
        "open_tickets": open_tickets,
        "total_customers": total_customers,
        "pending_orders": pending_orders,
        "urgent_tickets": urgent_tickets,
    }


# ============================================================================
# PRODUCTS
# ============================================================================

@router.post("/products", response_model=ProductResponse)
async def create_product(
    payload: ProductCreate,
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Create product (staff only)."""
    product = Product(**payload.dict(exclude_unset=True))
    db.add(product)
    await db.flush()
    await db.commit()
    return product


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product_admin(
    product_id: str,
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Get product (staff only)."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    payload: ProductUpdate,
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Update product (staff only)."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(product, key, value)

    await db.flush()
    await db.commit()
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Delete product (staff only)."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await db.delete(product)
    await db.commit()


# ============================================================================
# CATEGORIES
# ============================================================================

@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    payload: dict,
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Create category (staff only)."""
    category = Category(**payload)
    db.add(category)
    await db.flush()
    await db.commit()
    return category


# ============================================================================
# ORDERS
# ============================================================================

@router.get("/orders")
async def list_orders(
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """List all orders (staff only)."""
    query = select(Order)
    if status:
        query = query.where(Order.status == status)
    query = query.order_by(Order.placed_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    orders = result.scalars().all()
    return [
        {
            "id": str(o.id),
            "number": o.number,
            "customer_id": str(o.customer_id),
            "status": o.status,
            "subtotal": float(o.subtotal),
            "shipping_amount": float(o.shipping_amount),
            "tax_amount": float(o.tax_amount),
            "total": float(o.total),
            "currency": o.currency,
            "placed_at": o.placed_at.isoformat() if o.placed_at else None,
        }
        for o in orders
    ]


@router.get("/orders/{order_id}")
async def get_order_admin(
    order_id: str,
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Get order details (staff only)."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return {
        "id": str(order.id),
        "number": order.number,
        "customer_id": str(order.customer_id),
        "status": order.status,
        "subtotal": float(order.subtotal),
        "shipping_amount": float(order.shipping_amount),
        "tax_amount": float(order.tax_amount),
        "total": float(order.total),
        "currency": order.currency,
        "placed_at": order.placed_at.isoformat() if order.placed_at else None,
    }


@router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    payload: dict,
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Update order status (staff only)."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    new_status = payload.get("status")
    order.status = new_status
    await db.flush()

    # Emit event based on new status
    event_map = {
        "shipped": EventType.ORDER_SHIPPED,
        "delivered": EventType.ORDER_DELIVERED,
        "cancelled": EventType.ORDER_CANCELLED,
    }
    if new_status in event_map:
        await emit_event(
            db,
            event_map[new_status],
            "order",
            order.id,
            {"order_number": order.number, "status": new_status},
        )

    await db.commit()
    return {"message": "Order updated"}


@router.post("/orders/{order_id}/ship")
async def ship_order(
    order_id: str,
    payload: dict = {},
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Create shipment + label, mark order shipped, emit order.shipped event."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status not in ("pending", "confirmed"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot ship order with status '{order.status}'")

    carrier = payload.get("carrier", random.choice(CARRIERS))
    label = create_label(order.number, carrier)

    shipment = Shipment(
        order_id=order.id,
        carrier=carrier,
        tracking_number=label["tracking_number"],
        status="picked_up",
        label_url=label["label_url"],
        estimated_delivery=label["estimated_delivery"],
        shipped_at=datetime.now(timezone.utc),
    )
    db.add(shipment)
    await db.flush()

    db.add(TrackingEvent(
        shipment_id=shipment.id,
        status="picked_up",
        location="Sender",
        description="Label created and parcel collected",
        occurred_at=datetime.now(timezone.utc),
    ))

    order.status = "shipped"
    await db.flush()

    await emit_event(
        db,
        EventType.ORDER_SHIPPED,
        "order",
        order.id,
        {
            "order_number": order.number,
            "tracking_number": label["tracking_number"],
            "carrier": carrier,
            "estimated_delivery": label["estimated_delivery"].isoformat(),
        },
    )

    await db.commit()
    return {
        "shipment_id": str(shipment.id),
        "tracking_number": label["tracking_number"],
        "carrier": carrier,
        "status": "picked_up",
        "estimated_delivery": label["estimated_delivery"].isoformat(),
        "label_url": label["label_url"],
    }


@router.post("/shipments/{shipment_id}/advance")
async def advance_shipment(
    shipment_id: str,
    payload: dict = {},
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Advance shipment to next tracking state (for testing)."""
    result = await db.execute(select(Shipment).where(Shipment.id == shipment_id))
    shipment = result.scalars().first()
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")

    force_fail = payload.get("force_fail", False)
    event_data = advance_tracking(shipment.current_status if hasattr(shipment, 'current_status') else shipment.status, force_fail=force_fail)

    if not event_data["advanced"]:
        return {"message": "Already in terminal state", "status": shipment.status}

    shipment.status = event_data["status"]

    db.add(TrackingEvent(
        shipment_id=shipment.id,
        status=event_data["status"],
        location=event_data["location"],
        description=event_data["description"],
        occurred_at=event_data["occurred_at"],
    ))

    if event_data["status"] == "delivered":
        shipment.delivered_at = event_data["occurred_at"]
        result2 = await db.execute(select(Order).where(Order.id == shipment.order_id))
        order = result2.scalars().first()
        if order:
            order.status = "delivered"
            await db.flush()
            await emit_event(
                db,
                EventType.ORDER_DELIVERED,
                "order",
                order.id,
                {"order_number": order.number, "tracking_number": shipment.tracking_number},
            )

    await db.commit()
    return {
        "shipment_id": str(shipment.id),
        "status": event_data["status"],
        "location": event_data["location"],
        "description": event_data["description"],
    }


# ============================================================================
# SUPPORT TICKETS
# ============================================================================

@router.get("/support/tickets", response_model=list[SupportTicketResponse])
async def list_support_tickets(
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """List all support tickets (staff only)."""
    query = select(SupportTicket)
    if status:
        query = query.where(SupportTicket.status == status)
    query = query.order_by(SupportTicket.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/support/tickets/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    payload: dict,
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Assign support ticket to staff member (staff only)."""
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    ticket.assigned_to_id = payload.get("assigned_to_id")
    await db.flush()
    await db.commit()
    return {"message": "Ticket assigned"}


# ============================================================================
# CAMPAIGNS
# ============================================================================

@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    payload: CampaignCreate,
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Create marketing campaign (staff only)."""
    campaign = Campaign(**payload.dict(exclude_unset=True), created_by_id=staff.id)
    db.add(campaign)
    await db.flush()
    await db.commit()
    return campaign


@router.get("/campaigns", response_model=list[CampaignResponse])
async def list_campaigns(
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """List campaigns (staff only)."""
    result = await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    return result.scalars().all()


# ============================================================================
# PAGES
# ============================================================================

@router.post("/pages", response_model=PageResponse)
async def create_page(
    payload: PageCreate,
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Create CMS page (staff only)."""
    page = Page(**payload.dict(exclude_unset=True))
    db.add(page)
    await db.flush()
    await db.commit()
    return page


# ============================================================================
# API KEYS
# ============================================================================

@router.post("/api-keys", response_model=ApiKeyCreateResponse)
async def create_api_key(
    payload: dict,
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Create API key for agent auth (staff only)."""
    key, key_hash = generate_api_key()
    api_key = ApiKey(
        name=payload.get("name"),
        key_hash=key_hash,
        scopes=payload.get("scopes", []),
    )
    db.add(api_key)
    await db.flush()
    await db.commit()
    return {**api_key.__dict__, "key": key}


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys (staff only)."""
    result = await db.execute(select(ApiKey).where(ApiKey.revoked_at.is_(None)))
    return result.scalars().all()


# ============================================================================
# ROLES & PERMISSIONS
# ============================================================================

@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """List all roles (staff only)."""
    result = await db.execute(select(Role))
    return result.scalars().all()


@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """List all permissions (staff only)."""
    result = await db.execute(select(Permission))
    return result.scalars().all()


# ============================================================================
# CUSTOMERS
# ============================================================================

@router.get("/customers")
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    staff: StaffUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """List all customers (staff only)."""
    result = await db.execute(
        select(Customer).order_by(Customer.created_at.desc()).offset(skip).limit(limit)
    )
    customers = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "email": c.email,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in customers
    ]
