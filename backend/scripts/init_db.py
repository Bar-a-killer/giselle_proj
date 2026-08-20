"""Create the SQLite schema. Safe to re-run (create_all is idempotent)."""

from app import models  # noqa: F401 - import so Base metadata knows about all tables
from app.db import Base, engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Schema created.")


if __name__ == "__main__":
    main()
