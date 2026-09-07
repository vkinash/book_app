"""HTTP tests for book API. RAG is mocked — these do not need Ollama."""

import uuid
from pathlib import Path

from httpx import AsyncClient


async def _upload(client: AsyncClient, sample_epub: Path, filename: str = "Good_Omens.epub"):
    """Helper: POST /book/upload_book with the sample EPUB."""
    response = await client.post(
        "/book/upload_book",
        files={"file": (filename, sample_epub.read_bytes(), "application/epub+zip")},
    )
    return response


async def test_upload_epub_and_list_books(client: AsyncClient, sample_epub: Path):
    """Upload a real .epub: 200, UUID id, original filename, then it shows in the list."""
    response = await _upload(client, sample_epub)
    assert response.status_code == 200
    data = response.json()
    uuid.UUID(data["id"])
    assert data["filename"] == "Good_Omens.epub"
    assert data["total_chunks"] == 3

    listed = await client.get("/book/stored_books")
    assert listed.status_code == 200
    books = listed.json()["books"]
    assert len(books) == 1
    assert books[0]["id"] == data["id"]
    assert books[0]["filename"] == "Good_Omens.epub"


async def test_upload_rejects_non_epub(client: AsyncClient):
    """Only .epub files are allowed; a .pdf must return 400."""
    response = await client.post(
        "/book/upload_book",
        files={"file": ("notes.pdf", b"%PDF-fake", "application/pdf")},
    )
    assert response.status_code == 400


async def test_reader_chapter_count_and_resource(client: AsyncClient, sample_epub: Path):
    """After upload: chapter HTML has title + book_id links; chapter_count > 0; container.xml serves."""
    uploaded = await _upload(client, sample_epub)
    book_id = uploaded.json()["id"]

    chapter = await client.get(
        "/book/chapter",
        params={"book_id": book_id, "chapter_index": 0},
    )
    assert chapter.status_code == 200
    assert "application/xhtml+xml" in chapter.headers["content-type"]
    body = chapter.text
    assert "chapter-nav" in body
    assert f"book_id={book_id}" in body
    assert "filename=" not in body

    counts = await client.get("/book/chapter_count", params={"book_id": book_id})
    assert counts.status_code == 200
    assert counts.json()["total_chapters"] > 0
    assert counts.json()["book_id"] == book_id

    # Every EPUB has this file; using it avoids guessing CSS paths.
    resource = await client.get(
        "/book/epub_resource",
        params={"book_id": book_id, "resource_path": "META-INF/container.xml"},
    )
    assert resource.status_code == 200
    assert b"rootfile" in resource.content.lower() or b"container" in resource.content.lower()


async def test_unknown_book_id_returns_404(client: AsyncClient):
    """A valid UUID that is not in the DB must 404 on chapter (not 500)."""
    missing = "550e8400-e29b-41d4-a716-446655440000"
    response = await client.get(
        "/book/chapter",
        params={"book_id": missing, "chapter_index": 0},
    )
    assert response.status_code == 404


async def test_chapter_404_when_file_missing_on_disk(
    client: AsyncClient, sample_epub: Path, books_dir: Path
):
    """DB row exists but the .epub was deleted: chapter must 404."""
    uploaded = await _upload(client, sample_epub)
    book_id = uploaded.json()["id"]
    (books_dir / f"{book_id}.epub").unlink()

    response = await client.get(
        "/book/chapter",
        params={"book_id": book_id, "chapter_index": 0},
    )
    assert response.status_code == 404


async def test_epub_resource_missing_path_returns_404(
    client: AsyncClient, sample_epub: Path
):
    """A path that is not inside the EPUB zip must 404, not 500."""
    uploaded = await _upload(client, sample_epub)
    book_id = uploaded.json()["id"]

    response = await client.get(
        "/book/epub_resource",
        params={"book_id": book_id, "resource_path": "not/a/real/file.css"},
    )
    assert response.status_code == 404


async def test_ask_missing_book_returns_404(client: AsyncClient):
    """/ask for a UUID that was never uploaded must 404."""
    response = await client.post(
        "/book/ask",
        params={
            "book_id": "550e8400-e29b-41d4-a716-446655440000",
            "question": "Who is Crowley?",
        },
    )
    assert response.status_code == 404


async def test_ask_rejects_non_uuid_book_id(client: AsyncClient):
    """book_id must be a UUID; a filename stem must not work (422 from FastAPI)."""
    response = await client.post(
        "/book/ask",
        params={"book_id": "Good_Omens_-_Neil_Gaiman", "question": "Who is Crowley?"},
    )
    assert response.status_code == 422


async def test_upload_still_succeeds_when_rag_fails(
    client: AsyncClient, sample_epub: Path, mock_rag
):
    """If RAG raises ValueError, upload still returns 200 with a warning."""
    mock_rag.process_book.side_effect = ValueError("Ollama is down")

    response = await _upload(client, sample_epub)
    assert response.status_code == 200
    data = response.json()
    assert "warning" in data
    uuid.UUID(data["id"])

    listed = await client.get("/book/stored_books")
    assert listed.json()["books"][0]["id"] == data["id"]
