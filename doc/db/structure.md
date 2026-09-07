# Database Structure

## Overview

The app stores user accounts, uploaded books, reading progress, highlights, vocabulary lookups, and cached AI responses. Everything lives in a single SQLite file (`book_app.db`) during development. The schema is designed to work with PostgreSQL later — switching databases is a connection-string change, not a rewrite.

## Tools

### SQLAlchemy

SQLAlchemy is the ORM (Object-Relational Mapper). It lets us define Python classes that map to database tables and query them with Python instead of raw SQL.

- **Version:** 2.0 with typed `Mapped` columns
- **Mode:** Async (uses `aiosqlite` driver for SQLite)
- **Location:** `db/` package — models in `db/models/`, session setup in `db/session.py`

### Alembic

Alembic manages database schema changes over time. Instead of editing the database manually, we write migration scripts that Alembic applies in order.

- **Config:** `alembic.ini` and `alembic/env.py`
- **Migrations:** `alembic/versions/`

## Tables

### `user`

User accounts. Extends the fastapi-users base class (Task 2 will wire auth to this table).

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `email` | String | Login email (unique) |
| `hashed_password` | String | Hashed password (never store plain text) |
| `is_active` | Boolean | Account enabled |
| `is_superuser` | Boolean | Admin flag |
| `is_verified` | Boolean | Email verified |
| `native_language` | String | User's native language code (e.g. `"sv"`) for AI translations |
| `cefr_level` | String | Self-assessed English level (`A1`–`C2`) for text simplification |

### `books`

Uploaded books owned by a user.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | Owner (FK → `user.id`) |
| `filename` | String | File name on disk |
| `title` | String | Title from EPUB metadata |
| `author` | String | Author from EPUB metadata |
| `format` | String | File format (default `"epub"`) |
| `uploaded_at` | DateTime | When the book was uploaded |

### `reading_state`

One row per user per book — tracks where the user stopped reading.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK → `user.id` |
| `book_id` | UUID | FK → `books.id` |
| `cfi_position` | String | EPUB CFI string for exact resume point |
| `progress_pct` | Float | Reading progress 0–100 for bookshelf UI |
| `updated_at` | DateTime | Last position update |

Unique constraint: `(user_id, book_id)` — one position per user per book.

### `highlights`

Text highlights saved by the user.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK → `user.id` |
| `book_id` | UUID | FK → `books.id` |
| `cfi_range` | String | Start/end CFI for the highlighted span |
| `text` | Text | Plain text of the highlight |
| `note` | Text | Optional user note |
| `color` | String | Highlight color (e.g. `"yellow"`) |
| `created_at` | DateTime | When highlight was saved |

### `vocab_entries`

Words or phrases the user looked up, with AI explanations.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK → `user.id` |
| `book_id` | UUID | FK → `books.id` |
| `phrase` | String | Word or phrase looked up |
| `context_sentence` | Text | Surrounding sentence for context |
| `explanation` | Text | AI-generated explanation |
| `created_at` | DateTime | When lookup was saved |

### `llm_cache`

Cached LLM responses to avoid repeated API calls and reduce cost.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `cache_key` | String | Hash of feature + model + level + text (unique) |
| `feature` | String | AI feature: `"explain"`, `"simplify"`, `"summarize"` |
| `model` | String | LLM model name |
| `response_json` | Text | Cached JSON response |
| `created_at` | DateTime | When entry was cached |

## Relationships

```
user
 ├── books (one user owns many books)
 ├── reading_state (one user has many reading positions)
 ├── highlights (one user has many highlights)
 └── vocab_entries (one user has many vocab lookups)

books
 ├── reading_state (one book has many user positions)
 ├── highlights (one book has many highlights)
 └── vocab_entries (one book has many vocab lookups)

llm_cache — standalone, no foreign keys (shared across all users)
```

Deleting a user cascades to their books, reading state, highlights, and vocab entries. Deleting a book cascades to its related rows.

## How to Run Migrations

Apply all pending migrations:

```bash
uv run alembic upgrade head
```

After changing a model, generate a new migration:

```bash
uv run alembic revision --autogenerate -m "describe your change"
uv run alembic upgrade head
```

Roll back one migration:

```bash
uv run alembic downgrade -1
```

## Configuration

Database URL is set in `settings.py`:

```
sqlite+aiosqlite:///./book_app.db
```

Override via environment variable:

```
DATABASE_URL=sqlite+aiosqlite:///./book_app.db
```

The SQLite file is gitignored — each developer has their own local copy.

## Future Extensions

- **PostgreSQL:** Change `database_url` to `postgresql+asyncpg://...` — models use portable SQLAlchemy types, no model changes needed.
- **Redis cache:** The `llm_cache` table can serve as a persistent fallback; Redis can sit in front for hot lookups.
- **Auth (Task 2):** The `user` table already extends fastapi-users — auth routes plug in without schema changes.
