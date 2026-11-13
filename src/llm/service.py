from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.llm.client import LLMClient
from src.llm.prompts import load_prompt
from src.llm.schemas import BookEnrichmentInput, EnrichmentResult, LLMSettings, DEFAULT_ENRICH_PROMPT_VERSION, sanitize_payload


def get_llm_settings() -> LLMSettings:
    enabled = os.getenv("LLM_ENABLED", "true").strip().lower() not in {"0", "false", "off", "no"}
    stub = os.getenv("LLM_STUB", "0").strip().lower() in {"1", "true", "yes", "on"}
    log_path = os.getenv("LLM_LOG_PATH") or str(Path(__file__).resolve().parents[2] / "logs" / "llm_calls.jsonl")

    return LLMSettings(
        enabled=enabled,
        stub=stub,
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
        model=os.getenv("LLM_MODEL"),
        timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
        max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
        log_path=log_path,
    )


def _log_call(entry: dict[str, Any]) -> None:
    settings = get_llm_settings()
    log_path = Path(settings.log_path or str(Path(__file__).resolve().parents[2] / "logs" / "llm_calls.jsonl"))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def build_stub_enrichment(payload: dict[str, Any]) -> EnrichmentResult:
    cleaned = sanitize_payload(payload)
    title = str(cleaned.get("title") or "Untitled book").strip()
    author = str(cleaned.get("author") or "Unknown author").strip()
    category = str(cleaned.get("category") or cleaned.get("genre") or "General").strip()
    description = str(cleaned.get("description") or "").strip()

    if description:
        quality_flags = ["metadata_present", "description_available"]
        confidence = 0.92
        needs_review = False
    else:
        quality_flags = ["missing_description"]
        confidence = 0.74
        needs_review = True

    summary = (
        f"{title} by {author} appears to fit the {category} category. "
        "The record is sufficiently structured for enrichment, with a concise summary based on the provided metadata."
    )
    return EnrichmentResult(
        category=category,
        summary=summary,
        quality_flags=quality_flags,
        confidence=confidence,
        needs_review=needs_review,
    )


def _parse_response(raw_text: str) -> EnrichmentResult:
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("LLM response was empty")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM response was not valid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("LLM response must be a JSON object")

    try:
        return EnrichmentResult.model_validate(parsed)
    except ValidationError as exc:
        raise ValueError(f"LLM output failed validation: {exc}") from exc


def _repair_invalid_output(system_prompt: str, invalid_text: str, settings: LLMSettings, client: LLMClient) -> str:
    repair_prompt = (
        "Repair the following invalid JSON response so it matches the required schema exactly. "
        "Return only valid JSON and preserve the original semantics as closely as possible.\n\n"
        f"INVALID_RESPONSE:\n{invalid_text}"
    )
    repaired_text = client.complete(system_prompt, repair_prompt)
    return repaired_text


def enrich_book_payload(payload: dict[str, Any]) -> EnrichmentResult:
    settings = get_llm_settings()

    if not settings.enabled:
        raise RuntimeError("LLM functionality is disabled by configuration")

    validated = BookEnrichmentInput.model_validate(payload)
    cleaned = sanitize_payload(validated.model_dump(exclude_none=True, by_alias=False))

    if settings.stub:
        result = build_stub_enrichment(cleaned)
        _log_call({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_version": DEFAULT_ENRICH_PROMPT_VERSION,
            "mode": "stub",
            "stub": True,
            "enabled": settings.enabled,
            "success": True,
            "repair_used": False,
            "input": cleaned,
            "output": result.model_dump(),
        })
        return result

    prompt_text = load_prompt(DEFAULT_ENRICH_PROMPT_VERSION)
    client = LLMClient(base_url=settings.base_url, api_key=settings.api_key, model=settings.model, timeout_seconds=settings.timeout_seconds)
    user_content = json.dumps(cleaned, separators=(",", ":"), ensure_ascii=False)

    raw_response = client.complete(prompt_text, user_content)
    try:
        result = _parse_response(raw_response)
        _log_call({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_version": DEFAULT_ENRICH_PROMPT_VERSION,
            "mode": "live",
            "stub": False,
            "enabled": settings.enabled,
            "success": True,
            "repair_used": False,
            "input": cleaned,
            "output": result.model_dump(),
        })
        return result
    except ValueError:
        if settings.max_retries < 1:
            raise
        repair_text = _repair_invalid_output(prompt_text, raw_response, settings, client)
        try:
            repaired_result = _parse_response(repair_text)
            _log_call({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prompt_version": DEFAULT_ENRICH_PROMPT_VERSION,
                "mode": "live",
                "stub": False,
                "enabled": settings.enabled,
                "success": True,
                "repair_used": True,
                "input": cleaned,
                "output": repaired_result.model_dump(),
            })
            return repaired_result
        except ValueError as exc:
            _log_call({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prompt_version": DEFAULT_ENRICH_PROMPT_VERSION,
                "mode": "live",
                "stub": False,
                "enabled": settings.enabled,
                "success": False,
                "repair_used": True,
                "input": cleaned,
                "error": str(exc),
                "raw_output": repair_text,
            })
            raise RuntimeError("LLM output could not be repaired to a valid schema") from exc
