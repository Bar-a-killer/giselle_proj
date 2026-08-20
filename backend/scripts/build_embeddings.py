"""Recompute embeddings for every venue in the DB (or just the ones missing/stale)."""

from app.db import SessionLocal
from app.services.embeddings import get_venue_embedder, recompute_venue_embeddings


def main() -> None:
    session = SessionLocal()
    try:
        embedder = get_venue_embedder()
        updated = recompute_venue_embeddings(session, embedder, venue_ids=None)
        print(f"Recomputed embeddings for {updated} venues")
    finally:
        session.close()


if __name__ == "__main__":
    main()
