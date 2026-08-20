import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Review, Venue


@dataclass
class IngestSummary:
    venues_seen: int = 0
    venues_created: int = 0
    reviews_seen: int = 0
    reviews_created: int = 0
    touched_venue_ids: set[str] | None = None

    def __post_init__(self):
        if self.touched_venue_ids is None:
            self.touched_venue_ids = set()


def _venue_id(entry: dict) -> str | None:
    return entry.get("place_id") or entry.get("cid") or None


def _parse_published_at(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _review_text(review: dict) -> str | None:
    return review.get("text_original") or review.get("Description") or None


def _review_rating(review: dict) -> int | None:
    if review.get("rating_float"):
        return round(review["rating_float"])
    if review.get("Rating"):
        return review["Rating"]
    return None


def _review_author(review: dict) -> str | None:
    return review.get("Name") or None


def _review_id(venue_id: str, review: dict) -> str:
    explicit = review.get("review_id")
    if explicit:
        return explicit
    # Basic (non -extra-reviews) reviews don't always carry a stable review_id.
    # Derive a stable fallback from content so re-ingesting the same scrape dedupes cleanly.
    basis = "|".join(
        [venue_id, review.get("Name") or "", review.get("Description") or "", review.get("When") or ""]
    )
    return "fallback-" + hashlib.sha256(basis.encode()).hexdigest()[:16]


def _upsert_venue(session: Session, venue_id: str, entry: dict) -> bool:
    existing = session.get(Venue, venue_id)
    categories = entry.get("categories") or []
    fields = dict(
        title=entry.get("title") or "(untitled)",
        category=entry.get("category"),
        categories_json=json.dumps(categories),
        address=entry.get("address"),
        latitude=entry.get("latitude"),
        longitude=entry.get("longitude") or entry.get("longtitude"),
        google_rating=entry.get("review_rating"),
        google_review_count=entry.get("review_count"),
        raw_json=json.dumps(entry),
        scraped_at=datetime.utcnow(),
    )
    if existing:
        for key, value in fields.items():
            setattr(existing, key, value)
        return False
    session.add(Venue(id=venue_id, **fields))
    return True


def _upsert_review(session: Session, venue_id: str, review: dict) -> bool:
    review_id = _review_id(venue_id, review)
    existing = session.execute(
        select(Review).where(Review.venue_id == venue_id, Review.review_id == review_id)
    ).scalar_one_or_none()
    if existing:
        return False
    session.add(
        Review(
            venue_id=venue_id,
            review_id=review_id,
            author_name=_review_author(review),
            rating=_review_rating(review),
            text=_review_text(review),
            published_at=_parse_published_at(review.get("published_at")),
        )
    )
    return True


def ingest_entries(entries: list[dict], session: Session) -> IngestSummary:
    summary = IngestSummary()
    for entry in entries:
        venue_id = _venue_id(entry)
        if not venue_id:
            continue
        summary.venues_seen += 1
        created = _upsert_venue(session, venue_id, entry)
        if created:
            summary.venues_created += 1

        reviews = entry.get("user_reviews_extended") or entry.get("user_reviews") or []
        venue_touched = False
        for review in reviews:
            summary.reviews_seen += 1
            if _upsert_review(session, venue_id, review):
                summary.reviews_created += 1
                venue_touched = True
        if venue_touched:
            summary.touched_venue_ids.add(venue_id)

    session.commit()
    return summary


def ingest_file(path: Path, session: Session) -> IngestSummary:
    # gosom/google-maps-scraper's -json flag actually emits JSON-lines (one object per line) in
    # practice, not a single JSON array - handle both shapes the same way scraper_runner does.
    from app.services.scraper_runner import load_scrape_results

    return ingest_entries(load_scrape_results(path), session)
