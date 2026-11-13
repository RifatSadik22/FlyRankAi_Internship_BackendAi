from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .fetcher import DEFAULT_DELAY_SECONDS, DEFAULT_TIMEOUT_SECONDS, DEFAULT_USER_AGENT, fetch_url
from .normalizer import build_clean_record
from .parser import discover_catalogue_pages
from .reporter import build_run_report
from .storage import write_json

DEFAULT_TARGET_URL = "https://books.toscrape.com/"
SCRAPER_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = SCRAPER_ROOT / "cache"
OUTPUT_DIR = SCRAPER_ROOT / "output"


def parse_detail_record(html: str, product_url: str, source_page: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title_element = soup.select_one("article.product_page h1")
    title = title_element.get_text(" ", strip=True) if title_element else ""

    price_element = soup.select_one(".price_color")
    price_text = price_element.get_text(" ", strip=True) if price_element else ""

    availability_element = soup.select_one(".availability")
    availability_text = (
        availability_element.get_text(" ", strip=True)
        if availability_element
        else ""
    )

    rating_element = soup.select_one(".star-rating")
    rating_text = ""
    if rating_element:
        possible_names = {"one": "One", "two": "Two", "three": "Three", "four": "Four", "five": "Five"}
        classes = rating_element.get("class", [])
        for value in classes:
            value_lower = value.lower()
            if value_lower in possible_names:
                rating_text = possible_names[value_lower]
                break

    description_element = soup.select_one("#product_description + p")
    description = (
        description_element.get_text(" ", strip=True)
        if description_element
        else None
    )

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc),
    }


def scrape_books(
    target_url: str = DEFAULT_TARGET_URL,
    *,
    cache_dir: Path = CACHE_DIR,
    output_dir: Path = OUTPUT_DIR,
) -> dict:
    start_time = datetime.now(timezone.utc)
    cache_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = DEFAULT_USER_AGENT

    pages_fetched = 0
    cache_hits = 0

    def fetch_with_telemetry(url: str) -> str:
        nonlocal pages_fetched, cache_hits
        html, state, payload_size = fetch_url(
            url,
            cache_dir=cache_dir,
            session=session,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            user_agent=DEFAULT_USER_AGENT,
            use_cache=True,
            delay_seconds=DEFAULT_DELAY_SECONDS,
        )
        if state == "FETCH":
            pages_fetched += 1
        elif state == "CACHE HIT":
            cache_hits += 1
        print(f"{state}: {payload_size} bytes :: {url}")
        return html

    page_urls, discovered = discover_catalogue_pages(
        target_url,
        fetch_with_telemetry,
        max_pages=3,
    )

    raw_records: list[dict] = []
    failed_pages: list[dict] = []
    invalid_records: list[dict] = []
    valid_records: list[dict] = []
    seen_product_urls: set[str] = set()

    for product_url, source_page in discovered:
        try:
            detail_html = fetch_with_telemetry(product_url)
            raw_record = parse_detail_record(detail_html, product_url, source_page)
            raw_records.append(raw_record)
        except Exception as exc:  # pragma: no cover - network failure path
            failed_pages.append({"url": product_url, "error": str(exc)})

    for raw_record in raw_records:
        try:
            normalized = build_clean_record(raw_record)
            product_key = normalized["product_url"]
            if product_key in seen_product_urls:
                raise ValueError(f"duplicate product_url: {product_key}")
            seen_product_urls.add(product_key)
            valid_records.append(normalized)
        except Exception as exc:  # pragma: no cover - validation path
            invalid_records.append(
                {"product_url": raw_record.get("product_url"), "error": str(exc), "raw_record": raw_record}
            )

    write_json(output_dir / "books.json", valid_records)
    write_json(output_dir / "errors.json", invalid_records)

    duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
    run_report = build_run_report(
        start_time=start_time,
        duration_seconds=duration_seconds,
        catalogue_pages=len(page_urls),
        discovered_urls=len(discovered),
        unique_urls=len(valid_records),
        pages_fetched=pages_fetched,
        cache_hits=cache_hits,
        valid_records=len(valid_records),
        invalid_records=len(invalid_records),
        failed_pages=len(failed_pages),
    )
    write_json(output_dir / "run-report.json", run_report)

    print(f"catalogue_pages={len(page_urls)}")
    print(f"discovered={len(discovered)}")
    print(f"unique_urls={len(valid_records)}")
    print(f"detail_pages={len(raw_records)}")
    if valid_records:
        print(json.dumps(valid_records[0], ensure_ascii=False, indent=2))

    return run_report


if __name__ == "__main__":
    scrape_books()
