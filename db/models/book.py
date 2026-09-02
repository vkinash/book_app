from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.highlight import Highlight
    from db.models.reading_state import ReadingState
    from db.models.user import User
    from db.models.vocab_entry import VocabEntry


class Book(Base):
    """An uploaded book owned by a user."""

    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    author: Mapped[str | None] = mapped_column(String(512), nullable=True)
    format: Mapped[str] = mapped_column(String(10), nullable=False, default="epub")
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="books")
    reading_states: Mapped[list[ReadingState]] = relationship(back_populates="book")
    highlights: Mapped[list[Highlight]] = relationship(back_populates="book")
    vocab_entries: Mapped[list[VocabEntry]] = relationship(back_populates="book")
