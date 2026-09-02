from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes.books import router as book_router
from db.session import dispose_engine, engine
from settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify database connectivity on startup
    async with engine.connect():
        pass
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


app.include_router(book_router)
