from fastapi.responses import Response, HTMLResponse
from fastapi import APIRouter, Query, HTTPException
from settings import settings
import httpx

from pydantic import BaseModel, Field
from typing import Optional, Literal
import os


router = APIRouter(
    prefix="/text",
    tags=["text"]
)

# Endpoint to serve resources from EPUB
@router.get("/en/word_definition")
async def get_english_definition(
        word: str = Query(...)
):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=404, detail="Word not found")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Dictionary service unavailable")

