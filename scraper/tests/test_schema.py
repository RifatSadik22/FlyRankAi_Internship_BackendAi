from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from scraper.src.schemas import BookRecord


VALID_RECORD = {
    "title": "A Light in the Attic",
    "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    "price_text": "£51.77",
    "price_gbp": 51.77,
    "availability_text": "In stock (22 available)",
    "rating_text": "Three",
    "rating": 3,
    "description": "A collection of poems and stories.",
    "source_page": "https://books.toscrape.com/catalogue/page-1.html",
    "fetched_at": datetime.now(timezone.utc),
}


def test_schema_accepts_valid_record() -> None:
    record = BookRecord.model_validate(VALID_RECORD)
    assert record.title == "A Light in the Attic"
    assert record.rating == 3


def test_schema_rejects_bad_product_url() -> None:
    payload = {**VALID_RECORD, "product_url": "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"}
    with pytest.raises(ValidationError):
        BookRecord.model_validate(payload)


def test_schema_rejects_invalid_rating_value() -> None:
    payload = {**VALID_RECORD, "rating": 0}
    with pytest.raises(ValidationError):
        BookRecord.model_validate(payload)


def test_schema_rejects_missing_description_if_not_optional() -> None:
    payload = {**VALID_RECORD}
    payload.pop("description")
    record = BookRecord.model_validate(payload)
    assert record.description is None
