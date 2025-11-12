from fastapi import FastAPI
from settings import settings

from api.routes.books import router as book_router
from api.routes.words import router as word_router


app = FastAPI(
    title=settings.app_name
)


@app.get("/")
async def index():
    return {
        "app_name": settings.app_name,
        "api_prefix": settings.api_prefix
    }


app.include_router(book_router)
app.include_router(word_router)
