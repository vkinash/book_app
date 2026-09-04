import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.book import Book
from db.models.user import User
from settings import settings


def book_file_path(book: Book) -> Path:
    """Return on-disk path for a book's EPUB file."""
    return settings.books_path / f"{book.id}.epub"


async def create_book(
    session: AsyncSession,
    user: User,
    filename: str,
    title: str | None,
    author: str | None,
    book_id: uuid.UUID | None = None,
) -> Book:
    """Insert a new book row owned by the user."""
    book = Book(
        id=book_id or uuid.uuid4(),
        user_id=user.id,
        filename=filename,
        title=title,
        author=author,
        format="epub",
    )
    session.add(book)
    await session.commit()
    await session.refresh(book)
    return book


async def list_books(session: AsyncSession, user_id: uuid.UUID) -> list[Book]:
    """List books for a user, newest first."""
    result = await session.execute(
        select(Book)
        .where(Book.user_id == user_id)
        .order_by(Book.uploaded_at.desc())
    )
    return list(result.scalars().all())


async def get_book(
    session: AsyncSession,
    book_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Book | None:
    """Load a single book owned by the user."""
    result = await session.execute(
        select(Book).where(Book.id == book_id, Book.user_id == user_id)
    )
    return result.scalar_one_or_none()
