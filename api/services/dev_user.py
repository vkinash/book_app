from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User
from settings import settings

_password_hash = PasswordHash.recommended()
_DEV_PASSWORD_PLACEHOLDER = "dev-not-for-login"


async def get_or_create_dev_user(session: AsyncSession) -> User:
    """Return the default dev user, creating it if missing."""
    result = await session.execute(
        select(User).where(User.email == settings.dev_user_email)
    )
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(
        email=settings.dev_user_email,
        hashed_password=_password_hash.hash(_DEV_PASSWORD_PLACEHOLDER),
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
