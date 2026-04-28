"""Customer endpoints: auth, orders, account, reviews."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from apps.api.dependencies import get_db
from apps.api.models import Customer, Order, OrderItem, Payment, Review
from apps.api.models.customer import Address
from apps.api.schemas import (
    CustomerCreate, CustomerLogin, CustomerResponse, SessionResponse,
    CustomerTOTPSetup, CustomerVerifyTOTP, OrderResponse, ReviewCreate, ReviewResponse,
    CheckoutCreate, CheckoutResponse,
)
from apps.api.auth import (
    hash_password, verify_password, create_session, generate_secret,
    get_totp_uri, verify_totp, require_customer
)
from apps.api.mocks.payment import charge
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


@router.get("/orders")
async def list_customer_orders(
    customer: Customer = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """List customer orders."""
    result = await db.execute(
        select(Order).where(Order.customer_id == customer.id).order_by(Order.placed_at.desc())
    )
    orders = result.scalars().all()
    return [
        {
            "id": str(o.id),
            "number": o.number,
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


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    payload: CheckoutCreate,
    customer: Customer = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Place an order: create address, order, run payment mock, emit event."""
    # Generate order number: ORD-YYYY-NNNNN
    result = await db.execute(func.count(Order.id))
    count = result.scalar() or 0
    year = datetime.now(timezone.utc).year
    order_number = f"ORD-{year}-{(count + 1):05d}"

    # Compute totals
    subtotal = sum(float(item.unit_price) * item.quantity for item in payload.items)
    shipping = 5.99 if subtotal < 100 else 0.0
    tax = round(subtotal * 0.20, 2)
    total = round(subtotal + shipping + tax, 2)

    # Create shipping address
    addr_data = payload.shipping_address
    address = Address(
        customer_id=customer.id,
        type="shipping",
        first_name=addr_data.first_name,
        last_name=addr_data.last_name,
        line1=addr_data.line1,
        line2=addr_data.line2,
        city=addr_data.city,
        state=addr_data.state,
        postal_code=addr_data.postal_code,
        country_code=addr_data.country_code,
        phone=addr_data.phone,
    )
    db.add(address)
    await db.flush()

    # Create order
    order = Order(
        number=order_number,
        customer_id=customer.id,
        shipping_address_id=address.id,
        status="pending",
        subtotal=subtotal,
        shipping_amount=shipping,
        tax_amount=tax,
        total=total,
        currency="EUR",
        notes=payload.notes,
    )
    db.add(order)
    await db.flush()

    # Create order items
    for item in payload.items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            sku_snapshot=item.sku_snapshot,
            name_snapshot=item.name_snapshot,
            unit_price=float(item.unit_price),
            quantity=item.quantity,
            total_price=float(item.unit_price) * item.quantity,
        ))

    # Run payment mock
    payment_result = charge(total, "EUR", payload.card_token)

    payment = Payment(
        order_id=order.id,
        provider="mock",
        provider_ref=payment_result["transaction_id"],
        status="succeeded" if payment_result["success"] else "failed",
        amount=total,
        currency="EUR",
        method="card",
        payment_metadata=payment_result,
    )
    db.add(payment)

    if payment_result["success"]:
        order.status = "confirmed"
        await emit_event(
            db,
            EventType.ORDER_PLACED,
            "order",
            order.id,
            {
                "order_number": order_number,
                "customer_id": str(customer.id),
                "total": total,
                "items": len(payload.items),
            },
        )
    else:
        order.status = "payment_failed"

    await db.commit()

    return CheckoutResponse(
        order_number=order_number,
        order_id=order.id,
        total=total,
        currency="EUR",
        payment_status=payment.status,
        payment_transaction_id=payment_result["transaction_id"],
        error=payment_result.get("error_message"),
    )
