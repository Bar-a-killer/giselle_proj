import json

import numpy as np

from app.models import Review, Venue, VenueEmbedding
from app.services.embeddings import TfidfVenueEmbedder, recompute_venue_embeddings


class StubVenueEmbedder:
    """Deterministic embedder used in tests so we don't download a real model."""

    dim = 3

    def embed_venue(self, reviews: list[str], attributes: dict) -> np.ndarray:
        vec = np.array([len(reviews), sum(len(r) for r in reviews), 1.0])
        norm = np.linalg.norm(vec)
        return vec / norm if norm else vec


def test_tfidf_embedder_produces_unit_norm_vectors():
    embedder = TfidfVenueEmbedder(max_features=32)
    embedder.fit(["great coffee and pastries", "loud steakhouse with good ribeye"])

    vec = embedder.embed_venue(["great coffee and friendly staff"], {"category": "Coffee shop"})

    assert vec.shape == (embedder.dim,)
    assert abs(np.linalg.norm(vec) - 1.0) < 1e-6


def test_tfidf_embedder_falls_back_to_category_when_no_reviews():
    embedder = TfidfVenueEmbedder(max_features=16)
    embedder.fit(["coffee shop reviews", "steakhouse reviews"])

    vec = embedder.embed_venue([], {"category": "Coffee shop"})

    assert vec.shape == (embedder.dim,)


def test_recompute_venue_embeddings_writes_rows(session):
    session.add(Venue(id="v1", title="Venue One", category="Coffee shop"))
    session.add(Review(venue_id="v1", review_id="r1", text="lovely quiet cafe"))
    session.add(Review(venue_id="v1", review_id="r2", text="great espresso"))
    session.add(Venue(id="v2", title="Venue Two (no reviews yet)", category="Steakhouse"))
    session.commit()

    updated = recompute_venue_embeddings(session, StubVenueEmbedder(), venue_ids=None)
    assert updated == 2

    emb1 = session.get(VenueEmbedding, "v1")
    assert emb1.review_count_used == 2
    vec1 = np.array(json.loads(emb1.vector_json))
    assert vec1.shape == (3,)
    assert abs(np.linalg.norm(vec1) - 1.0) < 1e-6

    emb2 = session.get(VenueEmbedding, "v2")
    assert emb2.review_count_used == 0  # cold start: falls back to category text, not a review


def test_recompute_venue_embeddings_updates_existing_row(session):
    session.add(Venue(id="v1", title="Venue One", category="Coffee shop"))
    session.add(Review(venue_id="v1", review_id="r1", text="lovely quiet cafe"))
    session.commit()

    recompute_venue_embeddings(session, StubVenueEmbedder(), venue_ids=["v1"])
    first_updated_at = session.get(VenueEmbedding, "v1").updated_at

    session.add(Review(venue_id="v1", review_id="r2", text="great espresso"))
    session.commit()
    recompute_venue_embeddings(session, StubVenueEmbedder(), venue_ids=["v1"])

    rows = session.query(VenueEmbedding).filter_by(venue_id="v1").all()
    assert len(rows) == 1  # updated in place, not duplicated
    assert rows[0].review_count_used == 2
    assert rows[0].updated_at >= first_updated_at
