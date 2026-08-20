import json

from sqlalchemy import select

from app.models import Review, Venue
from app.services.ingest import ingest_entries
from tests.conftest import FIXTURES_DIR


def _load_fixture():
    return json.loads((FIXTURES_DIR / "sample_gmaps_output.json").read_text())


def test_ingest_creates_venues_and_reviews(session):
    entries = _load_fixture()
    summary = ingest_entries(entries, session)

    assert summary.venues_seen == 3
    assert summary.venues_created == 3
    assert summary.reviews_created == 7  # 3 coffee + 2 steakhouse + 2 ramen

    venues = session.execute(select(Venue)).scalars().all()
    assert {v.title for v in venues} == {
        "Sunrise Coffee Roasters",
        "The Copper Ember Steakhouse",
        "Noodle & Broth Ramen House",
    }


def test_ingest_is_idempotent(session):
    entries = _load_fixture()
    ingest_entries(entries, session)
    summary2 = ingest_entries(entries, session)

    assert summary2.venues_created == 0
    assert summary2.reviews_created == 0
    reviews = session.execute(select(Review)).scalars().all()
    assert len(reviews) == 7


def test_ingest_handles_basic_reviews_without_review_id(session):
    entries = _load_fixture()
    ingest_entries(entries, session)

    ramen_reviews = session.execute(
        select(Review).where(Review.venue_id == "ChIJ_ramen_place_003")
    ).scalars().all()
    assert len(ramen_reviews) == 2
    assert all(r.review_id and r.review_id.startswith("fallback-") for r in ramen_reviews)
    assert {r.author_name for r in ramen_reviews} == {"Sam Osei", "Wei Zhang"}


def test_ingest_prefers_extended_review_text(session):
    entries = _load_fixture()
    ingest_entries(entries, session)

    review = session.execute(select(Review).where(Review.review_id == "r1")).scalar_one()
    assert "pour-over" in review.text
    assert review.rating == 5
    assert review.published_at is not None
