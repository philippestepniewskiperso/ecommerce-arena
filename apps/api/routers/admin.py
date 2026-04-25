"""Admin endpoints: CRUD operations for all resources with RBAC."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.dependencies import get_db
from apps.api.models import (
    Product, Category, StaffUser, Order, Payment, Shipment,
    SupportTicket, Campaign, Page, Banner, Role, Permission, ApiKey
)
from apps.api.schemas import (
    ProductResponse, ProductCreate, ProductUpdate, CategoryResponse,
    OrderResponse, PaymentResponse, ShipmentResponse, SupportTicketResponse,
    CampaignResponse, CampaignCreate, PageResponse, PageCreate,
    BannerResponse, RoleResponse, PermissionResponse, ApiKeyResponse, ApiKeyCreateResponse
)
from apps.api.auth import require_staff, generate_api_key, hash_api_key

router = APIRouter(prefix="/api/admin", tags=["admin"])


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

@router.get("/orders", response_model=list[OrderResponse])
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
    return result.scalars().all()


@router.get("/orders/{order_id}", response_model=OrderResponse)
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
    return order


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

    order.status = payload.get("status")
    await db.flush()
    await db.commit()
    return {"message": "Order updated"}


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
