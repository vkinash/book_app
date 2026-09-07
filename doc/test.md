# Tests

This project uses **pytest**. There are two layers:

| Layer | What it does | Needs Ollama? | Command |
|-------|----------------|---------------|---------|
| **Unit** | API and helpers, RAG mocked | No | `make test` |
| **Smoke** | Real embeddings + `/ask` | Yes (`embeddinggemma`, `gemma3:1b`) | `make test-smoke` |

Unit tests are the default. Run them after a code change, before starting the app. Smoke tests are optional and slower; they talk to a local Ollama server.

---

## How to run

Install dev dependencies (pytest, pytest-asyncio):

```bash
uv sync --dev
```

**Unit tests only** (verbose, each test name is printed):

```bash
make test
```

Same thing without Make:

```bash
uv run pytest tests -v -m "not smoke"
```

**Smoke tests** (Ollama must be running with both models):

```bash
make test-smoke
```

or:

```bash
uv run pytest tests -v -m smoke
```

Run everything (unit + smoke):

```bash
uv run pytest tests -v
```

Run one file or one test:

```bash
uv run pytest tests/test_helpers.py -v
uv run pytest tests/test_books_api.py::test_upload_epub_and_list_books -v
```

`-v` prints each test as `PASSED`, `FAILED`, or `SKIPPED`. `--tb=short` (set in `pyproject.toml`) keeps failure traces short.

---

## Files

```
tests/
  conftest.py          Shared fixtures (temp DB, temp books dir, HTTP client, RAG mock)
  test_helpers.py      Nav bar and EPUB URL rewriting (no HTTP)
  test_books_api.py    HTTP tests for /book/* with mocked RAG
  test_rag_smoke.py    One live upload + ask against Ollama
doc/test.md            This document
```

Pytest settings live in `pyproject.toml` under `[tool.pytest.ini_options]` (`pythonpath = ["."]` so `db` and `api` import correctly).

---

## Isolation

Tests **do not** use:

- `book_app.db`
- `books_stored/` as the upload destination (except reading one sample EPUB)
- `./chroma_db` for assertions (smoke writes Chroma into a temp folder)

Each test gets:

- A temporary SQLite database with a fresh schema and the default dev user
- A temporary `books_dir` (uploads land here as `{uuid}.epub`)
- A FastAPI app that mounts only the book router (not `run.py`, so production lifespan is not started)

The sample file is:

`books_stored/test/Good_Omens_-_Neil_Gaiman_amp_Terry_Pratchett.epub`

If that file is missing, tests that need it are **skipped**.

---

## Unit tests (mocked RAG)

`api.routes.books.rag_service` is replaced with an `AsyncMock`. `process_book` returns a fake `total_chunks`; `answer_question` returns a fake string. Ollama is never called.

### `test_helpers.py`

| Test | What it checks |
|------|----------------|
| `test_nav_shows_book_name_and_book_id_links` | Nav shows `Good Omens — Chapter 2 of 5`; prev/next URLs use `book_id`, not `filename` |
| `test_nav_escapes_special_characters_in_title` | `&` and `<` in the title become `&amp;` and `&lt;` |
| `test_rewrite_resource_urls_use_book_id_not_file_path` | CSS/image `href`/`src` rewrite to `/book/epub_resource?book_id=...` |

### `test_books_api.py`

| Test | What it checks |
|------|----------------|
| `test_upload_epub_and_list_books` | `POST /book/upload_book` → 200, UUID `id`, original filename; book appears in `GET /book/stored_books` |
| `test_upload_rejects_non_epub` | Uploading a `.pdf` → 400 |
| `test_reader_chapter_count_and_resource` | `/chapter` is XHTML with nav and `book_id` links; `/chapter_count` has `total_chapters > 0`; `/epub_resource` serves `META-INF/container.xml` |
| `test_unknown_book_id_returns_404` | Unknown UUID on `/chapter` → 404 |
| `test_chapter_404_when_file_missing_on_disk` | DB row exists, file deleted → `/chapter` 404 |
| `test_epub_resource_missing_path_returns_404` | Path not in the EPUB zip → 404 (not 500) |
| `test_ask_missing_book_returns_404` | `/ask` for an unknown UUID → 404 |
| `test_ask_rejects_non_uuid_book_id` | `/ask?book_id=Good_Omens_-_Neil_Gaiman` → 422 (filename stem is not allowed) |
| `test_upload_still_succeeds_when_rag_fails` | Mocked RAG raises `ValueError` → upload still 200 with `warning` |

---

## Smoke tests (live Ollama)

Marked `@pytest.mark.smoke`. They are **not** run by `make test`.

Before the test runs, the fixture calls `GET http://localhost:11434/api/tags`.

| Situation | Result |
|-----------|--------|
| Ollama not running (`httpx.ConnectError`) | Test **skipped** |
| Request times out (`httpx.TimeoutException`) | Test **skipped** |
| Models `embeddinggemma` or `gemma3:1b` missing | Test **skipped** |
| Models present | Test runs |

`test_upload_process_and_ask`:

1. Upload the sample EPUB (this runs real `process_book`: extract, chunk, embed, store in temp Chroma).
2. If upload returned a `warning`, call `POST /book/process_book` and require `total_chunks > 0`.
3. `POST /book/ask?book_id={uuid}&question=Who%20is%20Crowley` must return HTTP 200 and a non-empty `answer`.

This can take several minutes (embedding a whole book). The smoke HTTP client timeout is 300 seconds.

Required models:

```bash
ollama serve
ollama pull embeddinggemma
ollama pull gemma3:1b
```

---

## Reading terminal output

A passing unit run looks like:

```
tests/test_books_api.py::test_upload_epub_and_list_books PASSED
tests/test_helpers.py::test_nav_shows_book_name_and_book_id_links PASSED
...
====== N passed in Xs ======
```

Skipped smoke (when you run `make test-smoke` without Ollama):

```
tests/test_rag_smoke.py::test_upload_process_and_ask SKIPPED (Ollama is not running...)
```

Failed tests print a short traceback (`--tb=short`) under the test name.

---

## Exceptions in tests

Tests and fixtures catch only known types:

- `httpx.ConnectError` — Ollama is down
- `httpx.TimeoutException` — Ollama too slow

Missing sample EPUB is handled with `Path.is_file()` and `pytest.skip`, not a catch-all `except`. There is no `except Exception`.

---

## Makefile

| Target | Command |
|--------|---------|
| `make test` | `uv run pytest tests -v -m "not smoke"` |
| `make test-smoke` | `uv run pytest tests -v -m smoke` |
