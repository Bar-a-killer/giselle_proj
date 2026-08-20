from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # gosom place_id or cid
    title: Mapped[str] = mapped_column(String)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    categories_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    google_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    google_review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("venue_id", "review_id", name="uq_review_venue_review_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venue_id: Mapped[str] = mapped_column(String, ForeignKey("venues.id"), index=True)
    review_id: Mapped[str | None] = mapped_column(String, nullable=True)
    author_name: Mapped[str | None] = mapped_column(String, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class VenueEmbedding(Base):
    __tablename__ = "venue_embeddings"

    venue_id: Mapped[str] = mapped_column(String, ForeignKey("venues.id"), primary_key=True)
    model_name: Mapped[str] = mapped_column(String)
    vector_json: Mapped[str] = mapped_column(Text)
    review_count_used: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "venue_id", name="uq_like_user_venue"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    venue_id: Mapped[str] = mapped_column(String, ForeignKey("venues.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
