"""Shared fixtures: temp DB, temp books dir, HTTP client, mocked or live RAG."""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import db.models  # noqa: F401 — register tables on Base.metadata
from api.routes.books import router
from api.services.dev_user import get_or_create_dev_user
from db.base import Base
from db.session import get_async_session
from settings import settings

# One real EPUB from the project test folder. Tests copy/upload it into a temp dir.
SAMPLE_EPUB = (
    Path(__file__).resolve().parent.parent
    / "books_stored"
    / "test"
    / "Good_Omens_-_Neil_Gaiman_amp_Terry_Pratchett.epub"
)


def ollama_skip_reason() -> str | None:
    """Return a skip message if Ollama or the required models are missing."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
    except httpx.ConnectError:
        return "Ollama is not running at http://localhost:11434"
    except httpx.TimeoutException:
        return "Ollama did not respond in time"

    if response.status_code != 200:
        return f"Ollama /api/tags returned HTTP {response.status_code}"

    names = [model.get("name", "") for model in response.json().get("models", [])]
    has_embed = any("embeddinggemma" in name for name in names)
    has_llm = any("gemma3" in name for name in names)
    if not has_embed or not has_llm:
        return (
            "Need Ollama models embeddinggemma and gemma3:1b. "
            f"Found: {names}"
        )
    return None


@pytest.fixture
def sample_epub() -> Path:
    """Path to the sample EPUB, or skip if it is not on disk."""
    if not SAMPLE_EPUB.is_file():
        pytest.skip(f"Sample EPUB not found: {SAMPLE_EPUB}")
    return SAMPLE_EPUB


@pytest.fixture
def books_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point settings.books_dir at a temp folder so tests do not touch books_stored/."""
    path = tmp_path / "books"
    path.mkdir()
    monkeypatch.setattr(settings, "books_dir", str(path))
    return path


@pytest.fixture
async def session_maker(tmp_path: Path):
    """In-memory-like SQLite file in tmp, with a fresh schema and a dev user."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        await get_or_create_dev_user(session)
    yield maker
    await engine.dispose()


@pytest.fixture
def mock_rag(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Fake RAG so unit tests never call Ollama or Chroma."""
    mock = AsyncMock()
    mock.process_book.return_value = {
        "book_id": "test-id",
        "total_chunks": 3,
        "document_ids": ["1", "2", "3"],
    }
    mock.answer_question.return_value = "Crowley is a demon."
    monkeypatch.setattr("api.routes.books.rag_service", mock)
    return mock


@pytest.fixture
async def app(books_dir: Path, session_maker) -> FastAPI:
    """Minimal app: book routes only, test DB session, no production lifespan."""

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            yield session

    application = FastAPI()
    application.include_router(router)
    application.dependency_overrides[get_async_session] = override_session
    return application


@pytest.fixture
async def client(app: FastAPI, mock_rag: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for unit tests (RAG is mocked)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


@pytest.fixture
def require_ollama() -> None:
    """Skip smoke tests when Ollama or the required models are not available."""
    reason = ollama_skip_reason()
    if reason:
        pytest.skip(reason)


@pytest.fixture
def smoke_rag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, require_ollama: None):
    """Real RAGService, but Chroma files go under tmp_path."""
    from core.rag_service import RAGService
    from core.vector_store import VectorStore

    service = RAGService()
    service.vector_store = VectorStore(persist_directory=str(tmp_path / "chroma"))
    service.vector_store.set_embedding_function(service.embedding_service.embeddings)
    monkeypatch.setattr("api.routes.books.rag_service", service)
    return service


@pytest.fixture
async def smoke_client(
    app: FastAPI, smoke_rag
) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for smoke tests (live Ollama, temp Chroma). Long timeout for embed/LLM."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", timeout=300.0
    ) as http:
        yield http
