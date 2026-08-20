import json

import numpy as np

from app.models import Like, User, Venue, VenueEmbedding
from app.services.scoring import (
    MIN_LIKES_FOR_CONFIDENT_PERSONALIZATION,
    rank_venues_for_user,
    venue_confidence,
)


def _add_venue(
    session,
    venue_id: str,
    title: str,
    vector: list[float],
    google_rating: float = 4.0,
    latitude: float | None = None,
    longitude: float | None = None,
):
    session.add(
        Venue(
            id=venue_id,
            title=title,
            google_rating=google_rating,
            google_review_count=10,
            latitude=latitude,
            longitude=longitude,
        )
    )
    vec = np.array(vector)
    vec = vec / np.linalg.norm(vec)
    session.add(
        VenueEmbedding(
            venue_id=venue_id,
            model_name="test",
            vector_json=json.dumps(vec.tolist()),
            review_count_used=10,
        )
    )


def test_venue_confidence_thresholds():
    assert venue_confidence(0) == "low"
    assert venue_confidence(4) == "low"
    assert venue_confidence(5) == "medium"
    assert venue_confidence(19) == "medium"
    assert venue_confidence(20) == "high"


def test_ranking_falls_back_to_google_rating_with_no_likes(session):
    _add_venue(session, "cafe1", "Cafe One", [1, 0], google_rating=4.8)
    _add_venue(session, "steak1", "Steak One", [0, 1], google_rating=4.2)
    session.add(User(id=1, name="tester"))
    session.commit()

    personalized, reason, scored = rank_venues_for_user(session, 1)

    assert personalized is False
    assert "no liked venues" in reason
    assert [sv.venue.id for sv in scored] == ["cafe1", "steak1"]
    assert all(sv.score is None for sv in scored)


def test_ranking_stays_unpersonalized_below_like_threshold(session):
    _add_venue(session, "cafe1", "Cafe One", [1, 0])
    _add_venue(session, "steak1", "Steak One", [0, 1])
    session.add(User(id=1, name="tester"))
    session.add(Like(user_id=1, venue_id="cafe1"))
    session.commit()

    assert MIN_LIKES_FOR_CONFIDENT_PERSONALIZATION > 1
    personalized, reason, scored = rank_venues_for_user(session, 1)

    assert personalized is False
    assert "1 liked venue" in reason


def test_ranking_prefers_venues_similar_to_liked_venues(session):
    # three cafe-ish venues, three steak-ish venues, all clearly separated in vector space
    _add_venue(session, "cafe1", "Cafe One", [1, 0.05])
    _add_venue(session, "cafe2", "Cafe Two", [1, -0.05])
    _add_venue(session, "cafe3", "Cafe Three", [0.95, 0.1])
    _add_venue(session, "steak1", "Steak One", [0.05, 1])
    _add_venue(session, "steak2", "Steak Two", [-0.05, 1])
    session.add(User(id=1, name="tester"))
    for vid in ["cafe1", "cafe2", "cafe3"]:
        session.add(Like(user_id=1, venue_id=vid))
    session.commit()

    personalized, reason, scored = rank_venues_for_user(session, 1)

    assert personalized is True
    assert reason is None
    ranked_ids = [sv.venue.id for sv in scored]
    # the two steakhouses should rank behind all three cafes given cafe-only likes
    assert ranked_ids.index("steak1") > max(ranked_ids.index(c) for c in ["cafe1", "cafe2", "cafe3"])
    assert ranked_ids.index("steak2") > max(ranked_ids.index(c) for c in ["cafe1", "cafe2", "cafe3"])


def test_ranking_flips_when_liked_venues_change(session):
    _add_venue(session, "cafe1", "Cafe One", [1, 0.05])
    _add_venue(session, "cafe2", "Cafe Two", [1, -0.05])
    _add_venue(session, "cafe3", "Cafe Three", [0.95, 0.1])
    _add_venue(session, "steak1", "Steak One", [0.05, 1])
    _add_venue(session, "steak2", "Steak Two", [-0.05, 1])
    _add_venue(session, "steak3", "Steak Three", [0, 0.95])
    session.add(User(id=1, name="tester"))
    for vid in ["cafe1", "cafe2", "cafe3"]:
        session.add(Like(user_id=1, venue_id=vid))
    session.commit()

    _, _, scored_liking_cafes = rank_venues_for_user(session, 1)
    top_when_liking_cafes = scored_liking_cafes[0].venue.id
    assert top_when_liking_cafes.startswith("cafe")

    for vid in ["cafe1", "cafe2", "cafe3"]:
        like = session.query(Like).filter_by(user_id=1, venue_id=vid).one()
        session.delete(like)
    for vid in ["steak1", "steak2", "steak3"]:
        session.add(Like(user_id=1, venue_id=vid))
    session.commit()

    _, _, scored_liking_steaks = rank_venues_for_user(session, 1)
    top_when_liking_steaks = scored_liking_steaks[0].venue.id
    assert top_when_liking_steaks.startswith("steak")


def test_ranking_without_user_location_has_no_distance(session):
    _add_venue(session, "cafe1", "Cafe One", [1, 0], latitude=47.6, longitude=-122.3)
    _add_venue(session, "cafe2", "Cafe Two", [1, 0], latitude=47.7, longitude=-122.3)
    _add_venue(session, "cafe3", "Cafe Three", [1, 0], latitude=47.8, longitude=-122.3)
    session.add(User(id=1, name="tester"))
    for vid in ["cafe1", "cafe2", "cafe3"]:
        session.add(Like(user_id=1, venue_id=vid))
    session.commit()

    _, _, scored = rank_venues_for_user(session, 1)

    assert all(sv.distance_km is None for sv in scored)


def test_ranking_with_user_location_orders_nearby_first_but_score_stays_pure_similarity(session):
    # near/far are identical in taste-vector terms; only distance should separate their order
    _add_venue(session, "near", "Near Cafe", [1, 0], latitude=47.60, longitude=-122.30)
    _add_venue(session, "far", "Far Cafe", [1, 0], latitude=48.60, longitude=-122.30)
    _add_venue(session, "liked1", "Liked One", [1, 0], latitude=47.60, longitude=-122.30)
    _add_venue(session, "liked2", "Liked Two", [1, 0], latitude=47.60, longitude=-122.30)
    _add_venue(session, "liked3", "Liked Three", [1, 0], latitude=47.60, longitude=-122.30)
    session.add(User(id=1, name="tester"))
    for vid in ["liked1", "liked2", "liked3"]:
        session.add(Like(user_id=1, venue_id=vid))
    session.commit()

    _, _, scored = rank_venues_for_user(session, 1, user_lat=47.60, user_lon=-122.30)
    by_id = {sv.venue.id: sv for sv in scored}
    ranked_ids = [sv.venue.id for sv in scored]

    assert by_id["near"].distance_km is not None
    assert by_id["far"].distance_km is not None
    assert by_id["near"].distance_km < by_id["far"].distance_km
    # order reflects distance...
    assert ranked_ids.index("near") < ranked_ids.index("far")
    # ...but the displayed score is identical pure taste-similarity, unaffected by distance
    assert by_id["near"].score == by_id["far"].score


def test_ranking_score_matches_no_location_score_even_when_location_given(session):
    # same taste vectors either way; giving a location must not change the displayed score
    _add_venue(session, "cafe1", "Cafe One", [1, 0.05], latitude=47.60, longitude=-122.30)
    _add_venue(session, "steak1", "Steak One", [0.05, 1], latitude=48.60, longitude=-122.30)
    _add_venue(session, "liked1", "Liked One", [1, 0], latitude=47.60, longitude=-122.30)
    _add_venue(session, "liked2", "Liked Two", [1, 0], latitude=47.60, longitude=-122.30)
    _add_venue(session, "liked3", "Liked Three", [1, 0], latitude=47.60, longitude=-122.30)
    session.add(User(id=1, name="tester"))
    for vid in ["liked1", "liked2", "liked3"]:
        session.add(Like(user_id=1, venue_id=vid))
    session.commit()

    _, _, scored_no_location = rank_venues_for_user(session, 1)
    _, _, scored_with_location = rank_venues_for_user(session, 1, user_lat=47.60, user_lon=-122.30)

    scores_no_location = {sv.venue.id: sv.score for sv in scored_no_location}
    scores_with_location = {sv.venue.id: sv.score for sv in scored_with_location}
    assert scores_no_location == scores_with_location


def test_ranking_fallback_still_attaches_distance_without_scoring(session):
    _add_venue(session, "cafe1", "Cafe One", [1, 0], google_rating=4.8, latitude=47.60, longitude=-122.30)
    session.add(User(id=1, name="tester"))
    session.commit()

    personalized, _, scored = rank_venues_for_user(session, 1, user_lat=47.61, user_lon=-122.31)

    assert personalized is False
    assert scored[0].score is None
    assert scored[0].distance_km is not None
