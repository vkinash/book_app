from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.dev_user import get_or_create_dev_user
from db.models.user import User
from db.session import get_async_session


async def get_dev_user(
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """FastAPI dependency: default dev user until Task 2 auth."""
    return await get_or_create_dev_user(session)
