import json
from datetime import datetime
from typing import Protocol

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Review, Venue, VenueEmbedding


class VenueEmbedder(Protocol):
    """Turns a venue's reviews (+ attributes) into one L2-normalized vector.

    Swappable seam: once there's enough user-interaction data to train a real
    two-tower recommender, a TwoTowerVenueEmbedder can implement this same
    interface and drop in without touching ingest/scoring/API code.
    """

    dim: int

    def embed_venue(self, reviews: list[str], attributes: dict) -> np.ndarray: ...


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm


class SentenceTransformerVenueEmbedder:
    def __init__(self, model_name: str = settings.embedding_model_name):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        get_dim = getattr(self.model, "get_embedding_dimension", None) or self.model.get_sentence_embedding_dimension
        self.dim = get_dim()

    def embed_venue(self, reviews: list[str], attributes: dict) -> np.ndarray:
        texts = [r for r in reviews if r and r.strip()][:50]
        if not texts:
            category = attributes.get("category") or "place"
            texts = [f"A {category}."]
        vecs = self.model.encode(texts, normalize_embeddings=False, show_progress_bar=False)
        venue_vec = np.asarray(vecs).mean(axis=0)
        return _l2_normalize(venue_vec)


class TfidfVenueEmbedder:
    """Cheaper fallback that avoids the sentence-transformers/torch dependency.

    Must be fit once on a text corpus before use (see `fit`).
    """

    def __init__(self, max_features: int = 512):
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.vectorizer = TfidfVectorizer(max_features=max_features, stop_words="english")
        self.dim = max_features
        self._fitted = False

    def fit(self, corpus: list[str]) -> None:
        self.vectorizer.fit(corpus or ["placeholder"])
        self.dim = len(self.vectorizer.vocabulary_)
        self._fitted = True

    def embed_venue(self, reviews: list[str], attributes: dict) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("TfidfVenueEmbedder must be fit() on a corpus before use")
        texts = [r for r in reviews if r and r.strip()]
        if not texts:
            texts = [attributes.get("category") or "place"]
        matrix = self.vectorizer.transform(texts)
        venue_vec = np.asarray(matrix.mean(axis=0)).ravel()
        return _l2_normalize(venue_vec)


def get_venue_embedder() -> VenueEmbedder:
    if settings.embedder_backend == "tfidf":
        raise RuntimeError("TfidfVenueEmbedder requires fit() on a corpus; construct it directly.")
    return SentenceTransformerVenueEmbedder()


def recompute_venue_embeddings(
    session: Session, embedder: VenueEmbedder, venue_ids: list[str] | None = None
) -> int:
    """(Re)computes and stores embeddings for the given venues (or all venues if None)."""
    venue_query = select(Venue)
    if venue_ids is not None:
        if not venue_ids:
            return 0
        venue_query = venue_query.where(Venue.id.in_(venue_ids))
    venues = session.execute(venue_query).scalars().all()

    updated = 0
    for venue in venues:
        reviews = session.execute(select(Review).where(Review.venue_id == venue.id)).scalars().all()
        texts = [r.text for r in reviews if r.text]
        vector = embedder.embed_venue(texts, {"category": venue.category})

        existing = session.get(VenueEmbedding, venue.id)
        payload = dict(
            model_name=settings.embedding_model_name,
            vector_json=json.dumps(vector.tolist()),
            review_count_used=len(texts),
            updated_at=datetime.utcnow(),
        )
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
        else:
            session.add(VenueEmbedding(venue_id=venue.id, **payload))
        updated += 1

    session.commit()
    return updated
