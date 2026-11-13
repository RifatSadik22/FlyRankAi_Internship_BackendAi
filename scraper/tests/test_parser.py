from __future__ import annotations

from scraper.src.parser import discover_catalogue_pages, extract_catalogue_links


def test_extract_catalogue_links_uses_absolute_urls() -> None:
    html = '''
    <html><body>
        <article class="product_pod"><h3><a href="/catalogue/a-light-in-the-attic_1000/index.html">A Light</a></h3></article>
    </body></html>
    '''
    urls = extract_catalogue_links(html, "https://books.toscrape.com/")
    assert urls == ["https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"]


def test_duplicate_urls_are_removed() -> None:
    candidate_urls = [
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    ]
    assert list(dict.fromkeys(candidate_urls)) == [candidate_urls[0]]


def test_discover_catalogue_pages_stops_after_three_pages() -> None:
    pages = [
        "https://books.toscrape.com/",
        "https://books.toscrape.com/catalogue/page-2.html",
        "https://books.toscrape.com/catalogue/page-3.html",
    ]
    html_map = {
        pages[0]: '<html><body><article class="product_pod"><h3><a href="/catalogue/a-light-in-the-attic_1000/index.html">A</a></h3></article><li class="next"><a href="/catalogue/page-2.html">next</a></li></body></html>',
        pages[1]: '<html><body><article class="product_pod"><h3><a href="/catalogue/a-light-in-the-attic_1000/index.html">A</a></h3></article><li class="next"><a href="/catalogue/page-3.html">next</a></li></body></html>',
        pages[2]: '<html><body><article class="product_pod"><h3><a href="/catalogue/a-light-in-the-attic_1000/index.html">A</a></h3></article></body></html>',
    }

    def fetch_html(url: str):
        return html_map[url], "FETCH", len(html_map[url])

    page_urls, discovered = discover_catalogue_pages(pages[0], fetch_html, max_pages=3)
    assert page_urls == pages[:3]
    assert len(discovered) == 1


def test_malformed_html_is_handled_without_crashing() -> None:
    html = "<html><body><article class='product_pod'><h3><a href='/catalogue/nope'>Broken"
    urls = extract_catalogue_links(html, "https://books.toscrape.com/")
    assert urls == ["https://books.toscrape.com/catalogue/nope"]
