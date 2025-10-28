import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.routes.books import router as book_router


app = FastAPI()

BOOKS_DIR = "books_stored"

# Ensure books_test exists
os.makedirs(BOOKS_DIR, exist_ok=True)
# app.mount("/books", StaticFiles(directory=BOOKS_DIR), name="books")

@app.get("/")
async def index():
    return {"message": "api v1"}


app.include_router(book_router)
