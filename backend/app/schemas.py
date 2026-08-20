from datetime import datetime

from pydantic import BaseModel


class VenueOut(BaseModel):
    id: str
    title: str
    category: str | None
    address: str | None
    latitude: float | None
    longitude: float | None
    google_rating: float | None
    google_review_count: int | None
    distance_km: float | None = None

    model_config = {"from_attributes": True}


class ReviewOut(BaseModel):
    author_name: str | None
    rating: int | None
    text: str | None
    published_at: datetime | None

    model_config = {"from_attributes": True}


class VenueDetailOut(VenueOut):
    reviews: list[ReviewOut]
    embedding_confidence: str
    review_count_used: int


class UserOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    name: str


class ScrapeRequest(BaseModel):
    queries: list[str]
    depth: int = 5
    concurrency: int = 1
    extra_reviews: bool = True


class ScrapeJobOut(BaseModel):
    job_id: str
    status: str
    counts: dict | None = None
    error: str | None = None


class ScoredVenueOut(VenueOut):
    score: int | None
    confidence: str


class RankingOut(BaseModel):
    personalized: bool
    reason: str | None = None
    venues: list[ScoredVenueOut]
