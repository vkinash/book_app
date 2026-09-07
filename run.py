from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes.books import router as book_router
from api.services.dev_user import get_or_create_dev_user
from api.schemas.auth import UserCreate, UserRead, UserUpdate
from api.services.auth import auth_backend, fastapi_users
from db.session import async_session_maker, dispose_engine, engine
from settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect():
        pass
    async with async_session_maker() as session:
        await get_or_create_dev_user(session)
    yield
    await dispose_engine()


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)


@app.get("/")
async def index():
    return {
        "app_name": settings.app_name,
        "api_prefix": settings.api_prefix,
    }


# Book routes
app.include_router(book_router)

# Auth routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
