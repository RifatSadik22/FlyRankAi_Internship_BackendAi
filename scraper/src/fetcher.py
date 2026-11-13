from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

DEFAULT_USER_AGENT = (
    "FlyRankInternship-A9/1.0 (+https://github.com/RifatSadik22/FlyRankAi_Internship_BackendAi)"
)
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_DELAY_SECONDS = 0.5


def cache_path_for_url(url: str, cache_dir: Path) -> Path:
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path or path in {"catalogue", "catalogue/"}:
        return cache_dir / "catalogue-page-1.html"
    if path.endswith("/page-1.html") or path == "index.html":
        return cache_dir / "catalogue-page-1.html"
    if path.endswith("/page-2.html"):
        return cache_dir / "catalogue-page-2.html"
    if path.endswith("/page-3.html"):
        return cache_dir / "catalogue-page-3.html"

    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", path or parsed.netloc)
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return cache_dir / f"{digest}_{slug}.html"


def fetch_url(
    url: str,
    *,
    cache_dir: Path,
    session: requests.Session | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    user_agent: str = DEFAULT_USER_AGENT,
    use_cache: bool = True,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
) -> tuple[str, str, int]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_path_for_url(url, cache_dir)

    if use_cache and cache_file.exists():
        content = cache_file.read_text(encoding="utf-8")
        return content, "CACHE HIT", len(content.encode("utf-8"))

    if delay_seconds > 0:
        time.sleep(delay_seconds)

    client = session or requests.Session()
    response = client.get(
        url,
        headers={"User-Agent": user_agent},
        timeout=timeout,
    )
    if response.status_code != 200:
        raise requests.HTTPError(
            f"Request for {url} failed with status code {response.status_code}"
        )

    text = response.text
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(text, encoding="utf-8")
    return text, "FETCH", len(response.content)
