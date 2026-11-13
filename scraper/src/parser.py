from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def extract_catalogue_links(html: str, page_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for anchor in soup.select("article.product_pod h3 a"):
        href = anchor.get("href")
        if href:
            links.append(urljoin(page_url, href))
    return links


def discover_catalogue_pages(
    start_url: str,
    fetch_html,
    *,
    max_pages: int = 3,
) -> tuple[list[str], list[tuple[str, str]]]:
    page_urls: list[str] = []
    discovered: list[tuple[str, str]] = []
    current_url = start_url
    seen_urls: set[str] = set()

    while current_url and len(page_urls) < max_pages:
        payload = fetch_html(current_url)
        if isinstance(payload, tuple):
            html, status, size = payload
        else:
            html = payload
            status = "FETCH"
            size = len(html.encode("utf-8"))
        page_urls.append(current_url)

        for book_url in extract_catalogue_links(html, current_url):
            if book_url not in seen_urls:
                seen_urls.add(book_url)
                discovered.append((book_url, current_url))

        soup = BeautifulSoup(html, "html.parser")
        next_link = soup.select_one("li.next a")
        if next_link is None or not next_link.get("href"):
            break
        current_url = urljoin(current_url, next_link["href"])

    return page_urls, discovered
