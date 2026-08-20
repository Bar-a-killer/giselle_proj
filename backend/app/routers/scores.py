from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import User
from app.schemas import RankingOut, ScoredVenueOut, VenueOut
from app.services.scoring import rank_venues_for_user

router = APIRouter(prefix="/api/users", tags=["scores"])


@router.get("/{user_id}/ranking", response_model=RankingOut)
def get_ranking(
    user_id: int,
    limit: int = 50,
    lat: float | None = None,
    lon: float | None = None,
    session: Session = Depends(get_session),
):
    if not session.get(User, user_id):
        raise HTTPException(status_code=404, detail="user not found")

    personalized, reason, scored = rank_venues_for_user(session, user_id, user_lat=lat, user_lon=lon)
    venues_out = [
        ScoredVenueOut(
            **VenueOut.model_validate(sv.venue).model_dump(exclude={"distance_km"}),
            score=sv.score,
            confidence=sv.confidence,
            distance_km=sv.distance_km,
        )
        for sv in scored[:limit]
    ]
    return RankingOut(personalized=personalized, reason=reason, venues=venues_out)
