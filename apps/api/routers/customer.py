"""Customer endpoints: auth, orders, account, reviews."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.dependencies import get_db
from apps.api.models import Customer, Order, Review
from apps.api.schemas import (
    CustomerCreate, CustomerLogin, CustomerResponse, SessionResponse,
    CustomerTOTPSetup, CustomerVerifyTOTP, OrderResponse, ReviewCreate, ReviewResponse
)
from apps.api.auth import (
    hash_password, verify_password, create_session, generate_secret,
    get_totp_uri, verify_totp, require_customer
)
from apps.api.events import emit_event, EventType

router = APIRouter(prefix="/api/customer", tags=["customer"])


@router.post("/auth/signup", response_model=SessionResponse)
async def signup(payload: CustomerCreate, db: AsyncSession = Depends(get_db)):
    """Create customer account and return session."""
    # Check email not taken
    result = await db.execute(select(Customer).where(Customer.email == payload.email))
    if result.scalars().first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Create customer
    customer = Customer(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
    )
    db.add(customer)
    await db.flush()

    # Create session
    token, session = await create_session(db, "customer", customer.id, ttl_hours=720)

    # Emit event
    await emit_event(
        db,
        EventType.CUSTOMER_SIGNUP,
        "customer",
        customer.id,
        {"email": customer.email, "first_name": customer.first_name, "last_name": customer.last_name},
    )

    await db.commit()

    return {"token": token, "expires_at": session.expires_at}


@router.post("/auth/login", response_model=SessionResponse)
async def login(payload: CustomerLogin, db: AsyncSession = Depends(get_db)):
    """Login and return session."""
    result = await db.execute(select(Customer).where(Customer.email == payload.email))
    customer = result.scalars().first()
    if not customer or not verify_password(payload.password, customer.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if customer.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")

    token, session = await create_session(db, "customer", customer.id, ttl_hours=720)
    await db.commit()

    return {"token": token, "expires_at": session.expires_at}


@router.post("/auth/mfa/setup", response_model=CustomerTOTPSetup)
async def setup_mfa(customer: Customer = Depends(require_customer), db: AsyncSession = Depends(get_db)):
    """Generate TOTP secret for MFA setup."""
    secret = generate_secret()
    uri = get_totp_uri(secret, customer.email)
    return {"secret": secret, "uri": uri}


@router.post("/auth/mfa/verify")
async def verify_mfa(
    payload: CustomerVerifyTOTP,
    customer: Customer = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Enable MFA after verifying TOTP token."""
    if not verify_totp(customer.mfa_secret or "", payload.token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP token")

    customer.mfa_enabled = True
    await db.flush()
    await db.commit()
    return {"message": "MFA enabled"}


@router.get("/profile", response_model=CustomerResponse)
async def get_profile(customer: Customer = Depends(require_customer)):
    """Get customer profile."""
    return customer


@router.get("/orders", response_model=list[OrderResponse])
async def list_customer_orders(
    customer: Customer = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """List customer orders."""
    result = await db.execute(
        select(Order).where(Order.customer_id == customer.id).order_by(Order.placed_at.desc())
    )
    return result.scalars().all()


@router.get("/orders/{order_number}", response_model=OrderResponse)
async def get_customer_order(
    order_number: str,
    customer: Customer = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Get specific customer order."""
    result = await db.execute(
        select(Order).where(Order.number == order_number, Order.customer_id == customer.id)
    )
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.post("/reviews", response_model=ReviewResponse)
async def post_review(
    payload: ReviewCreate,
    customer: Customer = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Post product review."""
    # Check customer purchased product
    result = await db.execute(
        select(Order).join(Order.items).where(
            Order.customer_id == customer.id,
            Order.items.product_id == payload.product_id,
        )
    )
    if not result.scalars().first():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only review purchased products")

    review = Review(
        product_id=payload.product_id,
        customer_id=customer.id,
        rating=payload.rating,
        title=payload.title,
        body=payload.body,
        status="pending",
    )
    db.add(review)
    await db.flush()

    await emit_event(
        db,
        "review.created",
        "review",
        review.id,
        {"product_id": str(payload.product_id), "rating": payload.rating, "customer_id": str(customer.id)},
    )

    await db.commit()
    return review
