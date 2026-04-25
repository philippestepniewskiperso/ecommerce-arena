"""Pydantic schemas for request/response across all domains."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid

from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# AUTH & CUSTOMER
# ============================================================================

class CustomerBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None


class CustomerCreate(CustomerBase):
    password: str = Field(min_length=8)


class CustomerLogin(BaseModel):
    email: EmailStr
    password: str


class CustomerTOTPSetup(BaseModel):
    secret: str
    uri: str


class CustomerVerifyTOTP(BaseModel):
    token: str


class CustomerResponse(CustomerBase):
    id: uuid.UUID
    email_verified_at: Optional[datetime] = None
    mfa_enabled: bool
    status: str
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    token: str
    expires_at: datetime


class StaffUserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str


class StaffUserCreate(StaffUserBase):
    password: str = Field(min_length=8)


class StaffUserResponse(StaffUserBase):
    id: uuid.UUID
    status: str
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleResponse(RoleBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None


class PermissionResponse(PermissionBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


class ApiKeyCreate(BaseModel):
    name: str
    scopes: list[str] = []


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(ApiKeyResponse):
    key: str


# ============================================================================
# CATALOG
# ============================================================================

class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    position: int = 0


class CategoryResponse(CategoryBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    status: str = "draft"
    base_price: Decimal
    compare_price: Optional[Decimal] = None
    tags: list[str] = []
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    status: Optional[str] = None
    base_price: Optional[Decimal] = None
    compare_price: Optional[Decimal] = None
    tags: Optional[list[str]] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None


class ProductImageResponse(BaseModel):
    id: uuid.UUID
    url: str
    alt_text: Optional[str] = None
    position: int

    class Config:
        from_attributes = True


class ProductVariantBase(BaseModel):
    sku: str
    name: str
    attributes: Optional[dict] = None
    price_override: Optional[Decimal] = None
    weight_g: Optional[int] = None
    is_default: bool = False


class ProductVariantResponse(ProductVariantBase):
    id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ProductResponse(ProductBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    variants: list[ProductVariantResponse] = []
    images: list[ProductImageResponse] = []

    class Config:
        from_attributes = True


class ProductSearchResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    base_price: Decimal
    short_description: Optional[str] = None
    images: list[ProductImageResponse] = []

    class Config:
        from_attributes = True


class ReviewBase(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = None
    body: Optional[str] = None


class ReviewCreate(ReviewBase):
    product_id: uuid.UUID


class ReviewResponse(ReviewBase):
    id: uuid.UUID
    product_id: uuid.UUID
    customer_id: uuid.UUID
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# INVENTORY
# ============================================================================

class StockLevelResponse(BaseModel):
    id: uuid.UUID
    variant_id: uuid.UUID
    quantity: int
    reserved_quantity: int
    low_stock_threshold: int
    updated_at: datetime

    class Config:
        from_attributes = True


class StockMovementResponse(BaseModel):
    id: uuid.UUID
    variant_id: uuid.UUID
    type: str
    delta: int
    balance_after: int
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CUSTOMER PROFILE
# ============================================================================

class AddressBase(BaseModel):
    type: str = "shipping"
    first_name: str
    last_name: str
    line1: str
    line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: str
    country_code: str
    phone: Optional[str] = None
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressResponse(AddressBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ORDERS
# ============================================================================

class OrderItemBase(BaseModel):
    variant_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    sku_snapshot: str
    name_snapshot: str
    variant_name_snapshot: Optional[str] = None
    unit_price: Decimal
    quantity: int
    total_price: Decimal


class OrderItemResponse(OrderItemBase):
    id: uuid.UUID
    order_id: uuid.UUID

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    shipping_address_id: Optional[uuid.UUID] = None
    billing_address_id: Optional[uuid.UUID] = None
    status: str = "pending"
    subtotal: Decimal
    discount_amount: Decimal = Decimal("0")
    shipping_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total: Decimal
    currency: str = "EUR"
    notes: Optional[str] = None
    promo_code: Optional[str] = None


class OrderCreate(BaseModel):
    items: list[OrderItemBase]
    shipping_address_id: uuid.UUID
    billing_address_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    promo_code: Optional[str] = None


class OrderResponse(OrderBase):
    id: uuid.UUID
    number: str
    customer_id: uuid.UUID
    placed_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []

    class Config:
        from_attributes = True


class ReturnItemBase(BaseModel):
    order_item_id: uuid.UUID
    quantity: int
    reason: Optional[str] = None
    condition: Optional[str] = None


class ReturnRequestBase(BaseModel):
    order_id: uuid.UUID
    reason: str
    notes: Optional[str] = None


class ReturnRequestCreate(ReturnRequestBase):
    items: list[ReturnItemBase]


class ReturnRequestResponse(ReturnRequestBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    status: str
    refund_amount: Optional[Decimal] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# PAYMENT
# ============================================================================

class PaymentBase(BaseModel):
    order_id: uuid.UUID
    provider: str
    amount: Decimal
    currency: str = "EUR"
    method: Optional[str] = None


class PaymentResponse(PaymentBase):
    id: uuid.UUID
    status: str
    provider_ref: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SHIPPING
# ============================================================================

class TrackingEventBase(BaseModel):
    status: str
    location: Optional[str] = None
    description: Optional[str] = None
    occurred_at: datetime


class TrackingEventResponse(TrackingEventBase):
    id: uuid.UUID
    shipment_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ShipmentBase(BaseModel):
    order_id: uuid.UUID
    carrier: str
    tracking_number: Optional[str] = None
    status: str = "pending"


class ShipmentResponse(ShipmentBase):
    id: uuid.UUID
    label_url: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    tracking_events: list[TrackingEventResponse] = []

    class Config:
        from_attributes = True


# ============================================================================
# SUPPORT
# ============================================================================

class TicketMessageBase(BaseModel):
    body: str
    is_internal: bool = False


class TicketMessageResponse(TicketMessageBase):
    id: uuid.UUID
    ticket_id: uuid.UUID
    author_type: str
    author_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class SupportTicketBase(BaseModel):
    subject: str
    status: str = "open"
    priority: str = "medium"
    order_id: Optional[uuid.UUID] = None


class SupportTicketCreate(SupportTicketBase):
    pass


class SupportTicketResponse(SupportTicketBase):
    id: uuid.UUID
    number: str
    customer_id: uuid.UUID
    assigned_to_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    sla_deadline: Optional[datetime] = None
    messages: list[TicketMessageResponse] = []

    class Config:
        from_attributes = True


# ============================================================================
# MARKETING
# ============================================================================

class CampaignBase(BaseModel):
    name: str
    type: str = "email"
    status: str = "draft"
    subject: str
    body_html: str
    sender_name: str
    sender_email: EmailStr
    target_segment: Optional[dict] = None
    scheduled_at: Optional[datetime] = None


class CampaignCreate(CampaignBase):
    pass


class CampaignResponse(CampaignBase):
    id: uuid.UUID
    created_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# CMS
# ============================================================================

class PageBase(BaseModel):
    slug: str
    title: str
    body_html: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    status: str = "draft"


class PageCreate(PageBase):
    pass


class PageResponse(PageBase):
    id: uuid.UUID
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BannerBase(BaseModel):
    name: str
    image_url: str
    link_url: Optional[str] = None
    position: str = "homepage_hero"
    active: bool = True
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class BannerResponse(BannerBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# EVENTS & WEBHOOKS
# ============================================================================

class DomainEventResponse(BaseModel):
    id: uuid.UUID
    type: str
    aggregate_type: str
    aggregate_id: uuid.UUID
    payload: dict
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WebhookSubscriptionCreate(BaseModel):
    url: str
    events: list[str]
    secret: str


class WebhookSubscriptionResponse(BaseModel):
    id: uuid.UUID
    url: str
    events: list[str]
    active: bool
    created_at: datetime
    last_triggered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WebhookEventPayload(BaseModel):
    event_id: uuid.UUID
    type: str
    aggregate_type: str
    aggregate_id: uuid.UUID
    payload: dict
    created_at: datetime


# ============================================================================
# ERROR & PAGINATION
# ============================================================================

class ErrorResponse(BaseModel):
    detail: str
    status_code: int


class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 20


class PaginatedResponse(BaseModel):
    items: list
    total: int
    skip: int
    limit: int
