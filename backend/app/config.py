from pathlib import Path

from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
RAW_SCRAPE_DIR = DATA_DIR / "gmaps_raw"


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{DATA_DIR / 'app.db'}"
    scraper_binary: Path = BACKEND_DIR / "bin" / "gmaps-scraper"
    embedder_backend: str = "sentence-transformer"  # or "tfidf"
    embedding_model_name: str = "all-MiniLM-L6-v2"


settings = Settings()

DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_SCRAPE_DIR.mkdir(parents=True, exist_ok=True)
