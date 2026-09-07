import uuid

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    native_language: str | None = None
    cefr_level: str | None = None


class UserCreate(schemas.BaseUserCreate):
    native_language: str | None = None
    cefr_level: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    native_language: str | None = None
    cefr_level: str | None = None
