from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Review, Venue, VenueEmbedding
from app.schemas import ReviewOut, VenueDetailOut, VenueOut
from app.services.geo import venue_distance_km
from app.services.scoring import venue_confidence

router = APIRouter(prefix="/api/venues", tags=["venues"])


def _venue_out(venue: Venue, lat: float | None, lon: float | None) -> VenueOut:
    return VenueOut(
        **VenueOut.model_validate(venue).model_dump(exclude={"distance_km"}),
        distance_km=venue_distance_km(lat, lon, venue.latitude, venue.longitude),
    )


@router.get("", response_model=list[VenueOut])
def list_venues(
    q: str | None = None,
    category: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    session: Session = Depends(get_session),
):
    query = select(Venue)
    if q:
        query = query.where(Venue.title.ilike(f"%{q}%"))
    if category:
        query = query.where(Venue.category == category)
    venues = session.execute(query.order_by(Venue.title)).scalars().all()
    return [_venue_out(v, lat, lon) for v in venues]


@router.get("/{venue_id}", response_model=VenueDetailOut)
def get_venue(
    venue_id: str, lat: float | None = None, lon: float | None = None, session: Session = Depends(get_session)
):
    venue = session.get(Venue, venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="venue not found")

    reviews = session.execute(
        select(Review).where(Review.venue_id == venue_id).order_by(Review.published_at.desc())
    ).scalars().all()

    embedding = session.get(VenueEmbedding, venue_id)
    review_count_used = embedding.review_count_used if embedding else 0

    return VenueDetailOut(
        **_venue_out(venue, lat, lon).model_dump(),
        reviews=[ReviewOut.model_validate(r) for r in reviews[:20]],
        embedding_confidence=venue_confidence(review_count_used),
        review_count_used=review_count_used,
    )
