import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.models import UserSession


async def create_session(
    db: AsyncSession,
    principal_type: Literal["customer", "staff"],
    principal_id: uuid.UUID,
    ip: str | None = None,
    user_agent: str | None = None,
    ttl_hours: int = 24,
) -> tuple[str, UserSession]:
    """Create session token + DB record. Return (token, session_obj)."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    session = UserSession(
        principal_type=principal_type,
        principal_id=principal_id,
        token_hash=token_hash,
        ip=ip,
        user_agent=user_agent,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
    )
    db.add(session)
    await db.flush()

    return token, session


async def get_session(db: AsyncSession, token: str) -> UserSession | None:
    """Validate token and return session if active."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(UserSession).where(
            UserSession.token_hash == token_hash,
            UserSession.expires_at > now,
            UserSession.revoked_at.is_(None),
        )
    )
    return result.scalars().first()


async def revoke_session(db: AsyncSession, session_id: uuid.UUID) -> None:
    """Revoke a session."""
    result = await db.execute(select(UserSession).where(UserSession.id == session_id))
    session = result.scalars().first()
    if session:
        session.revoked_at = datetime.now(timezone.utc)
        await db.flush()
