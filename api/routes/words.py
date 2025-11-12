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

#---------Claude
# class SimplifyRequest(BaseModel):
#     text: str = Field(..., description="Text to simplify")
#     level: Literal["elementary", "intermediate", "advanced"] = Field(
#         default="intermediate",
#         description="Target reading level"
#     )
#     preserve_length: bool = Field(
#         default=False,
#         description="Try to keep similar length to original"
#     )
#
#
# class SimplifyResponse(BaseModel):
#     original_text: str
#     simplified_text: str
#     level: str
#     word_count_original: int
#     word_count_simplified: int
#
#
# # Text simplification using Claude API
# async def simplify_text_with_ai(
#         text: str,
#         level: str,
#         preserve_length: bool
# ) -> str:
#     """
#     Simplify text using Anthropic's Claude API
#     You need to set ANTHROPIC_API_KEY environment variable
#     """
#
#     # Level descriptions for the AI
#     level_descriptions = {
#         "elementary": "a 10-year-old child or A1-A2 language learner. Use very simple words, short sentences, and basic grammar.",
#         "intermediate": "a high school student or B1-B2 language learner. Use common vocabulary, clear sentence structures, and moderate complexity.",
#         "advanced": "a college student or C1 language learner. Use more sophisticated vocabulary while keeping sentences clear and well-structured."
#     }
#
#     length_instruction = (
#         "Try to keep the simplified version similar in length to the original."
#         if preserve_length
#         else "You can make it shorter or longer as needed for clarity."
#     )
#
#     prompt = f"""Simplify the following text for {level_descriptions[level]}
#
#             {length_instruction}
#
#             Rules:
#             - Maintain the core meaning and all important information
#             - Break down complex sentences into simpler ones
#             - Replace difficult words with easier synonyms
#             - Keep the same narrative flow and structure
#             - Don't add explanations or commentary
#             - Return ONLY the simplified text, nothing else
#
#             Original text:
#             {text}"""
#
#     api_key = settings.anthropic_api_key
#     if not api_key:
#         raise HTTPException(
#             status_code=500,
#             detail="ANTHROPIC_API_KEY not configured"
#         )
#
#     async with httpx.AsyncClient(timeout=60.0) as client:
#         try:
#             response = await client.post(
#                 "https://api.anthropic.com/v1/messages",
#                 headers={
#                     "x-api-key": api_key,
#                     "anthropic-version": "2023-06-01",
#                     "content-type": "application/json",
#                 },
#                 json={
#                     "model": "claude-sonnet-4-20250514",
#                     "max_tokens": 4096,
#                     "messages": [
#                         {"role": "user", "content": prompt}
#                     ]
#                 }
#             )
#             response.raise_for_status()
#             result = response.json()
#             return result["content"][0]["text"]
#
#         except httpx.HTTPStatusError as e:
#             raise HTTPException(
#                 status_code=e.response.status_code,
#                 detail=f"AI service error: {e.response.text}"
#             )
#         except httpx.RequestError as e:
#             raise HTTPException(
#                 status_code=503,
#                 detail="AI service unavailable"
#             )
#
#
# @router.post("/simplify", response_model=SimplifyResponse)
# async def simplify_text(request: SimplifyRequest):
#     """
#     Simplify text to specified reading level
#
#     Levels:
#     - elementary: For children or A1-A2 language learners
#     - intermediate: For teenagers or B1-B2 language learners
#     - advanced: For adults or C1 language learners
#     """
#
#     if not request.text.strip():
#         raise HTTPException(status_code=400, detail="Text cannot be empty")
#
#     # Simplify the text
#     simplified = await simplify_text_with_ai(
#         request.text,
#         request.level,
#         request.preserve_length
#     )
#
#     # Calculate word counts
#     original_words = len(request.text.split())
#     simplified_words = len(simplified.split())
#
#     return SimplifyResponse(
#         original_text=request.text,
#         simplified_text=simplified,
#         level=request.level,
#         word_count_original=original_words,
#         word_count_simplified=simplified_words
#     )
#
#
# @router.post("/simplify-chapter/{book_id}/{chapter_index}")
# async def simplify_chapter(
#         book_id: str,
#         chapter_index: int,
#         level: Literal["elementary", "intermediate", "advanced"] = "intermediate",
#         preserve_length: bool = False
# ):
#     """
#     Simplify a specific chapter from a book
#
#     This endpoint assumes you have a function to get chapter content.
#     Replace get_chapter_content() with your actual implementation.
#     """
#
#     # TODO: Replace with your actual chapter retrieval logic
#     # chapter_text = get_chapter_content(book_id, chapter_index)
#
#     # For now, raising an error - you need to integrate with your existing code
#     raise HTTPException(
#         status_code=501,
#         detail="Integrate this with your get_chapter_by_index endpoint"
#     )
#
#     # Example implementation once you have chapter retrieval:
#     # simplified = await simplify_text_with_ai(chapter_text, level, preserve_length)
#     # return {
#     #     "book_id": book_id,
#     #     "chapter_index": chapter_index,
#     #     "level": level,
#     #     "simplified_text": simplified,
#     #     "word_count_original": len(chapter_text.split()),
#     #     "word_count_simplified": len(simplified.split())
#     # }

#-----------OLLAMA
# class SimplifyRequest(BaseModel):
#     text: str = Field(..., description="Text to simplify")
#     level: Literal["elementary", "intermediate", "advanced"] = Field(
#         default="intermediate",
#         description="Target reading level"
#     )
#
#
# class SimplifyResponse(BaseModel):
#     original_text: str
#     simplified_text: str
#     level: str
#     word_count_original: int
#     word_count_simplified: int
#
#
# async def simplify_text_with_ollama(text: str, level: str) -> str:
#     """
#     Simplify text using Ollama (local, free)
#
#     Setup:
#     1. Install Ollama: https://ollama.ai
#     2. Run: ollama pull llama3.2
#     3. Ollama runs on http://localhost:11434 by default
#     """
#
#     level_descriptions = {
#         "elementary": "a 10-year-old child or A1-A2 language learner. Use very simple words, short sentences, and basic grammar.",
#         "intermediate": "a high school student or B1-B2 language learner. Use common vocabulary, clear sentence structures, and moderate complexity.",
#         "advanced": "a college student or C1 language learner. Use more sophisticated vocabulary while keeping sentences clear and well-structured."
#     }
#
#     prompt = f"""Simplify the following text for {level_descriptions[level]}
#
# Rules:
# - Maintain the core meaning and all important information
# - Break down complex sentences into simpler ones
# - Replace difficult words with easier synonyms
# - Keep the same narrative flow and structure
# - Don't add explanations or commentary
# - Return ONLY the simplified text, nothing else
#
# Original text:
# {text}"""
#
#     async with httpx.AsyncClient(timeout=120.0) as client:
#         try:
#             response = await client.post(
#                 "http://localhost:11434/api/generate",
#                 json={
#                     "model": "llama3.2",  # or "llama3.1", "mistral", etc.
#                     "prompt": prompt,
#                     "stream": False
#                 }
#             )
#             response.raise_for_status()
#             result = response.json()
#             return result["response"]
#
#         except httpx.ConnectError:
#             raise HTTPException(
#                 status_code=503,
#                 detail="Ollama not running. Start it with: ollama serve"
#             )
#         except httpx.HTTPStatusError as e:
#             raise HTTPException(
#                 status_code=e.response.status_code,
#                 detail=f"Ollama error: {e.response.text}"
#             )
#         except httpx.RequestError:
#             raise HTTPException(
#                 status_code=503,
#                 detail="Ollama service unavailable"
#             )
#
#
# @router.post("/simplify", response_model=SimplifyResponse)
# async def simplify_text(request: SimplifyRequest):
#     """Simplify text using local Ollama model (free)"""
#
#     if not request.text.strip():
#         raise HTTPException(status_code=400, detail="Text cannot be empty")
#
#     simplified = await simplify_text_with_ollama(request.text, request.level)
#
#     original_words = len(request.text.split())
#     simplified_words = len(simplified.split())
#
#     return SimplifyResponse(
#         original_text=request.text,
#         simplified_text=simplified,
#         level=request.level,
#         word_count_original=original_words,
#         word_count_simplified=simplified_words
#     )

#-------openai
# Models for request/response
class SimplifyRequest(BaseModel):
    text: str = Field(..., description="Text to simplify")
    level: Literal["elementary", "intermediate", "advanced"] = Field(
        default="intermediate",
        description="Target reading level"
    )
    preserve_length: bool = Field(
        default=False,
        description="Try to keep similar length to original"
    )


class SimplifyResponse(BaseModel):
    original_text: str
    simplified_text: str
    level: str
    word_count_original: int
    word_count_simplified: int


# Text simplification using OpenAI GPT
async def simplify_text_with_ai(
        text: str,
        level: str,
        preserve_length: bool
) -> str:
    """
    Simplify text using OpenAI GPT API

    Setup:
    1. Get API key at: https://platform.openai.com/api-keys
    2. Set environment variable: export OPENAI_API_KEY="your-key"
    3. Add credits to your OpenAI account (minimum $5)

    Models:
    - gpt-4o-mini: Fast and cheap (~$0.15 per 1M input tokens)
    - gpt-4o: Higher quality (~$2.50 per 1M input tokens)
    """

    # Level descriptions for the AI
    level_descriptions = {
        "elementary": "a 10-year-old child or A1-A2 language learner. Use very simple words, short sentences, and basic grammar.",
        "intermediate": "a high school student or B1-B2 language learner. Use common vocabulary, clear sentence structures, and moderate complexity.",
        "advanced": "a college student or C1 language learner. Use more sophisticated vocabulary while keeping sentences clear and well-structured."
    }

    length_instruction = (
        "Try to keep the simplified version similar in length to the original."
        if preserve_length
        else "You can make it shorter or longer as needed for clarity."
    )

    prompt = f"""Simplify the following text for {level_descriptions[level]}

{length_instruction}

Rules:
- Maintain the core meaning and all important information
- Break down complex sentences into simpler ones
- Replace difficult words with easier synonyms
- Keep the same narrative flow and structure
- Don't add explanations or commentary
- Return ONLY the simplified text, nothing else

Original text:
{text}"""

    api_key = settings.openai_api_key
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY not configured. Set it with: export OPENAI_API_KEY='your-key'"
        )

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",  # Use "gpt-4o" for better quality
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that simplifies text for language learners. You maintain the meaning while making the text easier to understand."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4096
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            if e.response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid OpenAI API key. Get one at: https://platform.openai.com/api-keys"
                )
            elif e.response.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded or insufficient credits. Add credits at: https://platform.openai.com/account/billing"
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"OpenAI API error: {error_detail}"
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail="OpenAI service unavailable. Please try again later."
            )


@router.post("/simplify", response_model=SimplifyResponse)
async def simplify_text(request: SimplifyRequest):
    """
    Simplify text to specified reading level using OpenAI GPT

    Levels:
    - elementary: For children or A1-A2 language learners
    - intermediate: For teenagers or B1-B2 language learners
    - advanced: For adults or C1 language learners

    Example:
    ```
    POST /simplify
    {
        "text": "The ephemeral nature of existence perplexed the philosopher.",
        "level": "elementary",
        "preserve_length": false
    }
    ```
    """

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    # Check text length (OpenAI has token limits)
    word_count = len(request.text.split())
    if word_count > 10000:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long ({word_count} words). Maximum is 10,000 words per request."
        )

    # Simplify the text
    simplified = await simplify_text_with_ai(
        request.text,
        request.level,
        request.preserve_length
    )

    # Calculate word counts
    original_words = len(request.text.split())
    simplified_words = len(simplified.split())

    return SimplifyResponse(
        original_text=request.text,
        simplified_text=simplified,
        level=request.level,
        word_count_original=original_words,
        word_count_simplified=simplified_words
    )


@router.post("/simplify-chapter/{book_id}/{chapter_index}")
async def simplify_chapter(
        book_id: str,
        chapter_index: int,
        level: Literal["elementary", "intermediate", "advanced"] = "intermediate",
        preserve_length: bool = False
):
    """
    Simplify a specific chapter from a book

    TODO: Integrate this with your existing chapter retrieval code

    Example integration:
    ```python
    # Get chapter text using your existing function
    chapter_text = get_chapter_content(book_id, chapter_index)

    # Simplify it
    simplified = await simplify_text_with_ai(chapter_text, level, preserve_length)

    return {
        "book_id": book_id,
        "chapter_index": chapter_index,
        "level": level,
        "simplified_text": simplified
    }
    ```
    """

    raise HTTPException(
        status_code=501,
        detail="TODO: Integrate this with your get_chapter_by_index endpoint. See function docstring for example."
    )