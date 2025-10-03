from fastapi import FastAPI

from api.routes.books import router as book_router


app = FastAPI()


@app.get("/")
async def index():
    return {"message": "api v1"}


app.include_router(book_router)
