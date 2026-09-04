"""Unit tests for nav HTML and EPUB resource URL rewriting (no HTTP, no Ollama)."""

from api.services.epub import EPUBData
from api.utils.books_navigation import add_navigation_buttons

BOOK_ID = "550e8400-e29b-41d4-a716-446655440000"


def test_nav_shows_book_name_and_book_id_links():
    """Chapter nav must show the title and use book_id in prev/next URLs."""
    html = add_navigation_buttons(
        html_content="<html><body><p>chapter</p></body></html>",
        current_index=1,
        total_chapters=5,
        book_id=BOOK_ID,
        book_name="Good Omens",
    )

    assert "Good Omens — Chapter 2 of 5" in html
    assert f"book_id={BOOK_ID}" in html
    assert "chapter_index=0" in html
    assert "chapter_index=2" in html
    assert "filename=" not in html


def test_nav_escapes_special_characters_in_title():
    """Titles with & or < must be escaped so the XHTML stays valid."""
    html = add_navigation_buttons(
        html_content="<p>no body tag</p>",
        current_index=0,
        total_chapters=1,
        book_id=BOOK_ID,
        book_name="War & Peace <draft>",
    )

    assert "War &amp; Peace &lt;draft&gt;" in html
    assert "War & Peace <draft>" not in html


async def test_rewrite_resource_urls_use_book_id_not_file_path():
    """CSS/image links must point at /book/epub_resource?book_id=..., not file_path."""
    html = await EPUBData.rewrite_resource_urls(
        html_content='<link href="../styles.css" /><img src="cover.jpg" />',
        current_xhtml_path="OEBPS/ch01.xhtml",
        book_id=BOOK_ID,
    )

    assert f"book_id={BOOK_ID}" in html
    assert "file_path=" not in html
    assert "epub_resource" in html
    assert "styles.css" in html
    assert "cover.jpg" in html
