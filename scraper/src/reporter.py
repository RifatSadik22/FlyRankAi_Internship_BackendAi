from __future__ import annotations

from datetime import datetime, timezone


def build_run_report(
    *,
    start_time: datetime,
    duration_seconds: float,
    catalogue_pages: int,
    discovered_urls: int,
    unique_urls: int,
    pages_fetched: int,
    cache_hits: int,
    valid_records: int,
    invalid_records: int,
    failed_pages: int,
) -> dict:
    return {
        "start_time": start_time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": round(duration_seconds, 3),
        "catalogue_pages": catalogue_pages,
        "discovered_urls": discovered_urls,
        "unique_urls": unique_urls,
        "pages_fetched": pages_fetched,
        "cache_hits": cache_hits,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "failed_pages": failed_pages,
    }
