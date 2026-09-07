from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.book import Book
    from db.models.highlight import Highlight
    from db.models.reading_state import ReadingState
    from db.models.vocab_entry import VocabEntry


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User account with auth fields from fastapi-users and app profile fields."""

    # User's native language code (e.g. "sv") for AI translations
    native_language: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Self-assessed English level (A1–C2) for text simplification
    cefr_level: Mapped[str | None] = mapped_column(String(5), nullable=True)

    books: Mapped[list[Book]] = relationship(back_populates="user")
    reading_states: Mapped[list[ReadingState]] = relationship(back_populates="user")
    highlights: Mapped[list[Highlight]] = relationship(back_populates="user")
    vocab_entries: Mapped[list[VocabEntry]] = relationship(back_populates="user")
