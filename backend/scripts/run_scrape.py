"""Manual one-off scrape + ingest + embed, without going through the API.

Usage:
    uv run python scripts/run_scrape.py --query "coffee in Capitol Hill Seattle" --depth 5
"""

import argparse
import uuid

from app.config import RAW_SCRAPE_DIR
from app.db import SessionLocal
from app.services.embeddings import get_venue_embedder, recompute_venue_embeddings
from app.services.ingest import ingest_entries
from app.services.scraper_runner import load_scrape_results, run_scrape


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", action="append", dest="queries", required=True, help="repeatable")
    parser.add_argument("--depth", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--no-extra-reviews", action="store_true")
    args = parser.parse_args()

    out_path = RAW_SCRAPE_DIR / f"{uuid.uuid4()}.json"
    print(f"Scraping {args.queries} -> {out_path}")
    run_scrape(
        args.queries,
        out_path,
        depth=args.depth,
        concurrency=args.concurrency,
        extra_reviews=not args.no_extra_reviews,
    )

    entries = load_scrape_results(out_path)
    print(f"Scraped {len(entries)} venue entries")

    session = SessionLocal()
    try:
        summary = ingest_entries(entries, session)
        print(
            f"Ingested: venues {summary.venues_created} new / {summary.venues_seen} seen, "
            f"reviews {summary.reviews_created} new / {summary.reviews_seen} seen"
        )

        embedder = get_venue_embedder()
        updated = recompute_venue_embeddings(session, embedder, list(summary.touched_venue_ids))
        print(f"Recomputed embeddings for {updated} venues")
    finally:
        session.close()


if __name__ == "__main__":
    main()
