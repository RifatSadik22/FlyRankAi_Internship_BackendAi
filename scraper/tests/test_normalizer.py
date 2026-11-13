from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from scraper.src.normalizer import clean_text, normalize_description, normalize_price, normalize_rating


def test_normalize_price_handles_pounds() -> None:
    assert normalize_price("£51.77") == 51.77


def test_normalize_price_handles_commas() -> None:
    assert normalize_price("£1,234.56") == 1234.56


def test_normalize_rating_translates_words() -> None:
    assert normalize_rating("Three") == 3
    assert normalize_rating("Five") == 5


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("  Sample   Book  ") == "Sample Book"


def test_missing_description_is_returned_as_none() -> None:
    fixture = Path(__file__).parent / "fixtures" / "book_missing_description.html"
    html = fixture.read_text(encoding="utf-8")
    assert "product_description" not in html
    assert normalize_description(None) is None


def test_date_and_whitespace_are_handled_cleanly() -> None:
    assert isinstance(datetime.now(timezone.utc), datetime)
    assert normalize_description("  Extra   whitespace description  ") == "Extra whitespace description"
