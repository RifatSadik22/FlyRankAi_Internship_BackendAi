from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator


class BookRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    rating: int
    description: str | None = None
    source_page: HttpUrl
    fetched_at: datetime

    @field_validator("product_url", "source_page")
    @classmethod
    def require_https(cls, value: HttpUrl) -> HttpUrl:
        if str(value).startswith("https://"):
            return value
        raise ValueError("URL must use HTTPS")

    @field_validator("rating")
    @classmethod
    def rating_must_be_in_range(cls, value: int) -> int:
        if value not in {1, 2, 3, 4, 5}:
            raise ValueError("rating must be between 1 and 5")
        return value


class ErrorRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_url: str | None = None
    error: str
    raw_record: dict
