# Import all models so Alembic autogenerate and Base.metadata see every table.
from db.models.book import Book
from db.models.highlight import Highlight
from db.models.llm_cache import LLMCache
from db.models.reading_state import ReadingState
from db.models.user import User
from db.models.vocab_entry import VocabEntry

__all__ = [
    "User",
    "Book",
    "ReadingState",
    "Highlight",
    "VocabEntry",
    "LLMCache",
]
