import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class LLMCache(Base):
    """Cached LLM responses to avoid repeated API calls."""

    __tablename__ = "llm_cache"
    __table_args__ = (UniqueConstraint("cache_key", name="uq_llm_cache_key"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # SHA-256 hash of feature + model + level + text
    cache_key: Mapped[str] = mapped_column(String(64), nullable=False)
    # AI feature name: "explain", "simplify", "summarize"
    feature: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    response_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
