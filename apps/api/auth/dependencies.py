import os
from typing import Annotated

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.auth.session import get_session
from apps.api.auth.rbac import has_permission, has_role
from apps.api.models import Customer, StaffUser, ApiKey
from apps.api.dependencies import get_db

EMAIL_VERIFY_SKIP = os.getenv("EMAIL_VERIFY_SKIP", "false").lower() == "true"


async def require_customer(
    authorization: Annotated[str, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> Customer:
    """Require valid customer session."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth token")

    token = authorization[7:]
    session = await get_session(db, token)
    if not session or session.principal_type != "customer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    result = await db.execute(select(Customer).where(Customer.id == session.principal_id))
    customer = result.scalars().first()
    if not customer or customer.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Customer inactive")

    if not EMAIL_VERIFY_SKIP and not customer.email_verified_at:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")

    return customer


async def require_staff(
    authorization: Annotated[str, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> StaffUser:
    """Require valid staff session."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth token")

    token = authorization[7:]
    session = await get_session(db, token)
    if not session or session.principal_type != "staff":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    result = await db.execute(select(StaffUser).where(StaffUser.id == session.principal_id))
    staff = result.scalars().first()
    if not staff or staff.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Staff inactive")

    return staff


async def require_api_key(
    authorization: Annotated[str, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    """Require valid API key."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    key = authorization[7:]
    key_hash = __import__("hashlib").sha256(key.encode()).hexdigest()

    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.revoked_at.is_(None),
        )
    )
    api_key = result.scalars().first()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    api_key.last_used_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    await db.flush()

    return api_key


async def require_staff_permission(required_permission: str):
    """Return dependency for staff + specific permission."""
    async def check(staff: StaffUser = Depends(require_staff), db: AsyncSession = Depends(get_db)) -> StaffUser:
        if not await has_permission(db, staff, required_permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission '{required_permission}' required")
        return staff
    return check


async def require_staff_role(required_role: str):
    """Return dependency for staff + specific role."""
    async def check(staff: StaffUser = Depends(require_staff), db: AsyncSession = Depends(get_db)) -> StaffUser:
        if not await has_role(db, staff, required_role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Role '{required_role}' required")
        return staff
    return check
