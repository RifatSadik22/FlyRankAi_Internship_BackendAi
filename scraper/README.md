# Polite Scraper

This project implements a small, polite scraper for the public Books to Scrape demo site.

## Target and classification

- Target website: https://books.toscrape.com/
- Purpose: the site is a deliberately public sandbox for scraping practice and training.
- Scope: only the first three catalogue pages and the 60 detail pages they discover.
- Data collected: book title, product URL, price, availability, rating, description, source catalogue page, and fetch timestamp.
- Actual robots.txt result: https://books.toscrape.com/robots.txt returned HTTP 404 Not Found. That means the site does not publish a robots.txt file for this exercise; it does not automatically grant permission, so the scraper stays within the small, explicit scope requested in the assignment.

This assignment did not need a browser because the required data is already present in the HTML returned by the server. A browser would only add unnecessary cost and complexity.

I will not reuse this code on another site without checking its rules and terms first.

## Politeness rules

- Use a descriptive User-Agent.
- Respect a 10-second request timeout.
- Stop after exactly three catalogue pages.
- Wait at least 0.5 seconds between real HTTP requests.
- Reuse cached HTML during development.
- Handle 403, 404, and other failures without crashing.
- Only collect the fields required for the assignment.

## Quick start

```bash
cd scraper
python -m pip install -r requirements.txt
python -m src.main
```

## Output files

- `output/books.json`: validated records.
- `output/errors.json`: invalid records and validation reasons.
- `output/run-report.json`: run summary.
- `cache/`: cached HTML used while developing the scraper.

## Record schema

Each valid record contains:

- title
- product_url
- price_text
- price_gbp
- availability_text
- rating_text
- rating
- description
- source_page
- fetched_at

Example:

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "rating": 3,
  "description": "A collection of poems...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-11-14T00:00:00Z"
}
```

## Validation and reporting

The scraper validates each normalized record with Pydantic before writing it to `books.json`. Invalid entries are recorded in `errors.json` and skipped. The run report records the start time, duration, catalog pages processed, discovered URLs, valid records, invalid records, failed pages, real requests, and cache hits.

## Ethics note

When a public API exists, prefer it. Never bypass logins, paywalls, or blocks. Collect only the data needed for the assignment and stop as soon as the task is complete.

## Limitations

This scraper intentionally stays within the first three catalogue pages and does not crawl the entire site. It is designed for the assignment and should not be repurposed elsewhere without checking the target site's rules and terms.
