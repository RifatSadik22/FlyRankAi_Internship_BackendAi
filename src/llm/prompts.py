from __future__ import annotations

from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompts"
DEFAULT_PROMPT_FILE = PROMPT_DIR / "enrich_prompt_v1.txt"


def load_prompt(prompt_version: str = "v1") -> str:
    prompt_file = PROMPT_DIR / f"enrich_prompt_{prompt_version}.txt"
    if not prompt_file.exists():
        if DEFAULT_PROMPT_FILE.exists():
            return DEFAULT_PROMPT_FILE.read_text(encoding="utf-8")
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8")
