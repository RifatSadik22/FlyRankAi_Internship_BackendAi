from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, StrictBool, StrictFloat, StrictStr, field_validator, model_validator


class BookEnrichmentInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str | None = None
    author: str | None = None
    description: str | None = None
    isbn: str | None = None
    category: str | None = None
    genre: str | None = None
    publication_year: int | None = None
    published_year: int | None = None
    page_count: int | None = None
    language: str | None = None

    @model_validator(mode="after")
    def ensure_identifying_fields(self) -> "BookEnrichmentInput":
        values = [
            self.title,
            self.author,
            self.description,
            self.isbn,
            self.category,
            self.genre,
        ]
        if not any(value is not None and str(value).strip() for value in values):
            raise ValueError(
                "At least one identifying field such as title, author, description, isbn, or category must be provided"
            )
        return self


class EnrichmentResult(BaseModel):
    category: StrictStr
    summary: StrictStr
    quality_flags: list[StrictStr]
    confidence: StrictFloat
    needs_review: StrictBool

    @field_validator("confidence")
    @classmethod
    def confidence_must_be_in_range(cls, value: float) -> float:
        if not 0.0 <= float(value) <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return float(value)

    @field_validator("quality_flags")
    @classmethod
    def quality_flags_must_not_be_empty(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("quality_flags must not be empty")
        return value


class LLMSettings(BaseModel):
    enabled: bool = True
    stub: bool = False
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    timeout_seconds: float = 30.0
    max_retries: int = 2
    log_path: str | None = None

    @property
    def effective_model(self) -> str:
        return self.model or "stub-model"


DEFAULT_ENRICH_PROMPT_VERSION = "v1"


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, str):
            cleaned[key] = value.strip()
        else:
            cleaned[key] = value
    return cleaned
