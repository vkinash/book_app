# API Reference

## Overview

The Book Reader API serves EPUB files, tracks book metadata in the database, and provides RAG-based Q&A. All book routes live under the `/book` prefix.

Books are identified by `book_id` (UUID). Metadata lives in the `books` table; the EPUB file is stored at `books_stored/{uuid}.epub`. `filename` in responses is the original upload name, not a lookup key.

**Base URL (local):** `http://localhost:8001`

**Auth:** Not implemented yet. All new uploads are owned by a default dev user (`dev@local.app`). Task 2 will add JWT authentication.

---

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | App info |
| POST | `/book/upload_book` | Upload EPUB + save to DB |
| GET | `/book/stored_books` | List DB books |
| GET | `/book/chapter` | Serve one chapter as HTML |
| GET | `/book/chapter_count` | Chapter count for a book |
| GET | `/book/epub_resource` | Serve EPUB assets (CSS, images) |
| POST | `/book/process_book` | Re-process book for RAG |
| POST | `/book/ask` | Ask a question about a book |

---

## POST /book/upload_book

Upload an EPUB file. Saves the file as `{uuid}.epub`, inserts a row in the `books` table, and runs RAG processing.

**Request:** `multipart/form-data` with field `file` (`.epub` only)

**Response (success):**
```json
{
  "message": "Book uploaded and processed successfully",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "good-omens.epub",
  "title": "Good Omens",
  "author": "Neil Gaiman",
  "total_chunks": 142
}
```

**Response (upload OK, RAG failed):** Same fields plus `"warning"` and `"error"`.

---

## GET /book/stored_books

List books from the database for the dev user.

**Response:**
```json
{
  "books": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "good-omens.epub",
      "title": "Good Omens",
      "author": "Neil Gaiman",
      "format": "epub",
      "uploaded_at": "2026-09-02T14:00:00+00:00"
    }
  ]
}
```

---

## GET /book/chapter

Return one chapter as XHTML with navigation buttons. The nav bar shows the book title (or original filename if title is missing).

**Query params:**

| Param | Required | Description |
|-------|----------|-------------|
| `book_id` | Yes | DB book UUID |
| `chapter_index` | No (default `0`) | Zero-based chapter index |

**Example:**
```
/book/chapter?book_id=550e8400-e29b-41d4-a716-446655440000&chapter_index=0
```

---

## GET /book/chapter_count

Return chapter count and spine file list.

**Query params:**

| Param | Required | Description |
|-------|----------|-------------|
| `book_id` | Yes | DB book UUID |

**Response:**
```json
{
  "book_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_chapters": 24,
  "chapters": ["OEBPS/ch01.xhtml", "..."]
}
```

---

## GET /book/epub_resource

Serve internal EPUB resources (CSS, images, fonts).

**Query params:**

| Param | Required | Description |
|-------|----------|-------------|
| `resource_path` | Yes | Path inside the EPUB zip |
| `book_id` | Yes | DB book UUID |

---

## POST /book/process_book

Re-run RAG indexing for a book.

**Query params:**

| Param | Required | Description |
|-------|----------|-------------|
| `book_id` | Yes | DB book UUID |

**Response:**
```json
{
  "message": "Book processed successfully",
  "book_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_chunks": 142
}
```

---

## POST /book/ask

Ask a question about a book using RAG.

**Query params:**

| Param | Required | Description |
|-------|----------|-------------|
| `book_id` | Yes | DB book UUID |
| `question` | Yes | Question text |

**Example:**
```
/book/ask?book_id=550e8400-e29b-41d4-a716-446655440000&question=Who%20is%20Crowley
```

**Response:**
```json
{
  "book_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "Who is Crowley?",
  "answer": "..."
}
```

---

## Example flow

1. **Upload:** `POST /book/upload_book` with EPUB file → get `id`
2. **List:** `GET /book/stored_books` → confirm book appears
3. **Read:** `GET /book/chapter?book_id={id}&chapter_index=0`
4. **Ask:** `POST /book/ask?book_id={id}&question=...`

---

## Related docs

- Database schema: [doc/db/structure.md](../db/structure.md)
- Run locally: `make dev` (port 8001)
