from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.models import StaffUser, Role, Permission


async def has_permission(db: AsyncSession, staff_user: StaffUser, required_permission: str) -> bool:
    """Check if staff user has a specific permission."""
    result = await db.execute(
        select(Permission).join(
            Role.permissions
        ).join(
            StaffUser.roles
        ).where(
            StaffUser.id == staff_user.id,
            Permission.name == required_permission,
        )
    )
    return result.scalars().first() is not None


async def has_role(db: AsyncSession, staff_user: StaffUser, required_role: str) -> bool:
    """Check if staff user has a specific role."""
    result = await db.execute(
        select(Role).join(
            StaffUser.roles
        ).where(
            StaffUser.id == staff_user.id,
            Role.name == required_role,
        )
    )
    return result.scalars().first() is not None


async def get_permissions(db: AsyncSession, staff_user: StaffUser) -> set[str]:
    """Get all permissions for a staff user."""
    result = await db.execute(
        select(Permission.name).join(
            Role.permissions
        ).join(
            StaffUser.roles
        ).where(
            StaffUser.id == staff_user.id,
        ).distinct()
    )
    return set(result.scalars().all())
