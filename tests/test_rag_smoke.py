"""Live Ollama + Chroma smoke test. Skip if models are not installed.

Run with: make test-smoke
"""

from pathlib import Path

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.smoke


async def test_upload_process_and_ask(smoke_client: AsyncClient, sample_epub: Path):
    """Upload a book, wait for real embeddings, then ask a question via /ask."""
    upload = await smoke_client.post(
        "/book/upload_book",
        files={
            "file": (
                "Good_Omens.epub",
                sample_epub.read_bytes(),
                "application/epub+zip",
            )
        },
    )
    assert upload.status_code == 200
    data = upload.json()
    book_id = data["id"]

    # Upload already runs process_book. If that failed, retry once via the endpoint.
    if "warning" in data:
        processed = await smoke_client.post(
            "/book/process_book",
            params={"book_id": book_id},
        )
        assert processed.status_code == 200
        assert processed.json()["total_chunks"] > 0
    else:
        assert data["total_chunks"] > 0

    asked = await smoke_client.post(
        "/book/ask",
        params={"book_id": book_id, "question": "Who is Crowley?"},
    )
    assert asked.status_code == 200
    answer = asked.json()["answer"]
    assert isinstance(answer, str)
    assert answer.strip() != ""
    assert asked.json()["book_id"] == book_id
