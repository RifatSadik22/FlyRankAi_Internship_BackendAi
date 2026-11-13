from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request


class LLMClient:
    """Minimal OpenAI-compatible client used for local testing and hidden tests."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None, timeout_seconds: float = 30.0):
        self.base_url = (base_url or os.getenv("LLM_BASE_URL") or "").rstrip("/")
        self.api_key = api_key or os.getenv("LLM_API_KEY") or "stub-key"
        self.model = model or os.getenv("LLM_MODEL") or "stub-model"
        self.timeout_seconds = timeout_seconds

    def _request_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.base_url:
            raise RuntimeError("LLM_BASE_URL is not configured")

        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except error.URLError as exc:  # pragma: no cover - exercised through dependency injection in tests
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("LLM provider response was not a JSON object")
        return parsed

    def complete(self, system_prompt: str, user_content: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.0,
        }
        response = self._request_json(payload)
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("LLM provider did not return any choices")
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("LLM provider returned a non-string message content")
        return content
