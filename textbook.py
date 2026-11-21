"""Textbook rules. Stage 1: navigation within a category (T R3).

No Streamlit, no SQL, no clock. Stage 2 adds practice here, with randomness only
from a random.Random passed in.
"""

from textbook_content import category_of


def _ids_around(article_id: str) -> list[str]:
    return [article.id for article in category_of(article_id).articles]


def neighbours(article_id: str) -> tuple[str | None, str | None]:
    """The previous and next article in the same category, or None at either end."""
    ids = _ids_around(article_id)
    index = ids.index(article_id)
    previous = ids[index - 1] if index > 0 else None
    following = ids[index + 1] if index < len(ids) - 1 else None
    return previous, following


def position(article_id: str) -> tuple[int, int]:
    """The article's place in its category, counted from 1, and the category size."""
    ids = _ids_around(article_id)
    return ids.index(article_id) + 1, len(ids)
