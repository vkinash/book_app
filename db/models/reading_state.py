from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.book import Book
    from db.models.user import User


class ReadingState(Base):
    """Tracks a user's reading position in a book."""

    __tablename__ = "reading_state"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_reading_state_user_book"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # EPUB CFI string for exact resume point
    cfi_position: Mapped[str] = mapped_column(String(1024), nullable=False)
    # Reading progress 0–100 for bookshelf UI
    progress_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="reading_states")
    book: Mapped[Book] = relationship(back_populates="reading_states")
