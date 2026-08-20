import json
import math
from dataclasses import dataclass

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Like, Venue, VenueEmbedding
from app.services.geo import venue_distance_km
from app.services.user_vector import get_user_embedder

MIN_LIKES_FOR_CONFIDENT_PERSONALIZATION = 3

LOW_REVIEW_THRESHOLD = 5
MEDIUM_REVIEW_THRESHOLD = 20

# How much the *sort order* (not the displayed score) is pulled toward "close by" vs "similar
# to what you like". The displayed score is always pure taste-similarity; distance only nudges
# where a venue lands in the list.
SIMILARITY_SORT_WEIGHT = 0.7
DISTANCE_SORT_WEIGHT = 0.3
# Distance score decays to ~37% at this many km, ~14% at 2x, ~5% at 3x.
DISTANCE_DECAY_KM = 5.0


def venue_confidence(review_count_used: int) -> str:
    if review_count_used < LOW_REVIEW_THRESHOLD:
        return "low"
    if review_count_used < MEDIUM_REVIEW_THRESHOLD:
        return "medium"
    return "high"


@dataclass
class ScoredVenue:
    venue: Venue
    score: int | None
    confidence: str
    distance_km: float | None = None


def _load_embedding_matrix(session: Session) -> tuple[list[str], np.ndarray, dict[str, int]]:
    rows = session.execute(select(VenueEmbedding)).scalars().all()
    venue_ids = [row.venue_id for row in rows]
    review_counts = {row.venue_id: row.review_count_used for row in rows}
    if not rows:
        return [], np.zeros((0, 0)), review_counts
    matrix = np.stack([np.array(json.loads(row.vector_json)) for row in rows])
    return venue_ids, matrix, review_counts


def _cosine_to_score(cosine_sim: float) -> int:
    return int(round(((cosine_sim + 1) / 2) * 100))


def _distance_score(distance_km: float) -> float:
    return 100 * math.exp(-distance_km / DISTANCE_DECAY_KM)


def _sort_key(similarity_score: int, distance_km: float | None) -> float:
    """Order-only blend of taste similarity and distance. Never used as the displayed score."""
    if distance_km is None:
        return similarity_score
    return SIMILARITY_SORT_WEIGHT * similarity_score + DISTANCE_SORT_WEIGHT * _distance_score(distance_km)


def rank_venues_for_user(
    session: Session,
    user_id: int,
    user_lat: float | None = None,
    user_lon: float | None = None,
) -> tuple[bool, str | None, list[ScoredVenue]]:
    """Returns (personalized, reason_if_not, scored_venues) sorted best-first.

    If user_lat/user_lon are given, each venue's distance is attached for display and used to
    break ties in sort order (closer venues rank a bit higher among similarly-scored ones), but
    the displayed `score` itself is always pure taste-similarity - distance never changes the
    number shown. With no user location, behavior is unchanged from before this existed.
    """
    venue_ids, matrix, review_counts = _load_embedding_matrix(session)
    venues_by_id = {v.id: v for v in session.execute(select(Venue)).scalars().all()}

    def distance_for(venue: Venue) -> float | None:
        return venue_distance_km(user_lat, user_lon, venue.latitude, venue.longitude)

    if not venue_ids:
        return False, "no venues scraped yet", []

    liked_venue_ids = set(
        session.execute(select(Like.venue_id).where(Like.user_id == user_id)).scalars().all()
    )

    if len(liked_venue_ids) < MIN_LIKES_FOR_CONFIDENT_PERSONALIZATION:
        reason = (
            "no liked venues yet - showing venues by Google rating"
            if not liked_venue_ids
            else f"only {len(liked_venue_ids)} liked venue(s) so far - pick a few more for real personalization"
        )
        fallback = sorted(
            (venues_by_id[vid] for vid in venue_ids if vid in venues_by_id),
            key=lambda v: (v.google_rating or 0, v.google_review_count or 0),
            reverse=True,
        )
        return False, reason, [
            ScoredVenue(v, None, venue_confidence(review_counts.get(v.id, 0)), distance_for(v)) for v in fallback
        ]

    id_to_row = {vid: i for i, vid in enumerate(venue_ids)}
    liked_rows = [id_to_row[vid] for vid in liked_venue_ids if vid in id_to_row]
    if not liked_rows:
        return False, "liked venues have no computed embeddings yet", []

    user_embedder = get_user_embedder()
    user_vec = user_embedder.embed_user([matrix[i] for i in liked_rows])
    if user_vec is None:
        return False, "could not build a preference vector", []

    sims = matrix @ user_vec
    scored = []
    for i, vid in enumerate(venue_ids):
        venue = venues_by_id.get(vid)
        if not venue:
            continue
        distance_km = distance_for(venue)
        similarity_score = _cosine_to_score(sims[i])
        scored.append(
            ScoredVenue(
                venue,
                similarity_score,
                venue_confidence(review_counts.get(vid, 0)),
                distance_km,
            )
        )
    scored.sort(key=lambda sv: _sort_key(sv.score, sv.distance_km), reverse=True)
    return True, None, scored
