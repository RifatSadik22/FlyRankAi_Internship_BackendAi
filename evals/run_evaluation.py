from __future__ import annotations

import json
from pathlib import Path

from src.llm.service import enrich_book_payload


def main() -> None:
    cases_path = Path(__file__).resolve().with_name("cases.json")
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    for case in cases:
        result = enrich_book_payload(case["input"])
        print(f"{case['name']}: {result.model_dump()}")


if __name__ == "__main__":
    main()
