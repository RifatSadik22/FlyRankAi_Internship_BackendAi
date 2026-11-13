from __future__ import annotations

import re
from datetime import datetime, timezone

from .schemas import BookRecord

RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


def normalize_price(raw_price: str) -> float:
    cleaned = raw_price.replace("\ufeff", "").replace("Â", "").replace("\xa0", " ").replace("£", "").replace(",", "").replace(" ", "").strip()
    if not cleaned:
        raise ValueError("price_text is empty")
    try:
        return float(cleaned)
    except ValueError as exc:
        raise ValueError(f"Invalid price value: {raw_price!r}") from exc


def normalize_rating(raw_rating: str) -> int:
    normalized = re.sub(r"[^A-Za-z]", "", raw_rating or "").lower()
    if normalized not in RATING_MAP:
        raise ValueError(f"Unsupported rating text: {raw_rating!r}")
    return RATING_MAP[normalized]


def clean_text(value: str | None) -> str:
    if value is None:
        raise ValueError("Required text field is missing")
    cleaned = " ".join(value.replace("\ufeff", "").replace("Â", "").replace("\xa0", " ").split())
    if not cleaned:
        raise ValueError("Required text field is blank")
    return cleaned


def normalize_description(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.replace("\ufeff", "").replace("\xa0", " ").split())
    return cleaned or None


def build_clean_record(raw_record: dict) -> dict:
    title = clean_text(raw_record.get("title"))
    product_url = clean_text(str(raw_record.get("product_url", "")))
    price_text = clean_text(raw_record.get("price_text"))
    availability = clean_text(raw_record.get("availability_text"))
    rating_text = clean_text(raw_record.get("rating_text"))
    source_page = clean_text(str(raw_record.get("source_page", "")))
    fetched_at = raw_record.get("fetched_at")
    if not isinstance(fetched_at, datetime):
        fetched_at = datetime.now(timezone.utc)

    payload = {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "price_gbp": normalize_price(price_text),
        "availability_text": availability,
        "rating_text": rating_text,
        "rating": normalize_rating(rating_text),
        "description": normalize_description(raw_record.get("description")),
        "source_page": source_page,
        "fetched_at": fetched_at,
    }
    return BookRecord.model_validate(payload).model_dump(mode="json")
