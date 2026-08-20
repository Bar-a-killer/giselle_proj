from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Like, User, Venue
from app.schemas import UserCreate, UserOut, VenueOut

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(session: Session = Depends(get_session)):
    return session.execute(select(User).order_by(User.name)).scalars().all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, session: Session = Depends(get_session)):
    user = User(name=payload.name)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="user with this name already exists")
    session.refresh(user)
    return user


def _get_user_or_404(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user


@router.get("/{user_id}/likes", response_model=list[VenueOut])
def list_likes(user_id: int, session: Session = Depends(get_session)):
    _get_user_or_404(session, user_id)
    venue_ids = session.execute(select(Like.venue_id).where(Like.user_id == user_id)).scalars().all()
    if not venue_ids:
        return []
    return session.execute(select(Venue).where(Venue.id.in_(venue_ids))).scalars().all()


@router.post("/{user_id}/likes/{venue_id}", status_code=204)
def like_venue(user_id: int, venue_id: str, session: Session = Depends(get_session)):
    _get_user_or_404(session, user_id)
    if not session.get(Venue, venue_id):
        raise HTTPException(status_code=404, detail="venue not found")
    existing = session.execute(
        select(Like).where(Like.user_id == user_id, Like.venue_id == venue_id)
    ).scalar_one_or_none()
    if not existing:
        session.add(Like(user_id=user_id, venue_id=venue_id))
        session.commit()


@router.delete("/{user_id}/likes/{venue_id}", status_code=204)
def unlike_venue(user_id: int, venue_id: str, session: Session = Depends(get_session)):
    _get_user_or_404(session, user_id)
    existing = session.execute(
        select(Like).where(Like.user_id == user_id, Like.venue_id == venue_id)
    ).scalar_one_or_none()
    if existing:
        session.delete(existing)
        session.commit()
