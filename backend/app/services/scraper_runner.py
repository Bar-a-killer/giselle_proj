import json
import subprocess
import tempfile
from pathlib import Path

from app.config import settings


class ScraperBinaryMissing(RuntimeError):
    pass


def run_scrape(
    queries: list[str],
    out_path: Path,
    *,
    depth: int = 5,
    concurrency: int = 1,
    extra_reviews: bool = True,
    lang: str = "en",
    timeout_seconds: int = 1800,
) -> Path:
    """Shell out to the gosom/google-maps-scraper binary. Writes JSON results to out_path."""
    if not settings.scraper_binary.exists():
        raise ScraperBinaryMissing(
            f"Scraper binary not found at {settings.scraper_binary}. Download a release from "
            "https://github.com/gosom/google-maps-scraper/releases and place it there (chmod +x)."
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("\n".join(queries))
        input_file = Path(f.name)

    argv = [
        str(settings.scraper_binary),
        "-input",
        str(input_file),
        "-results",
        str(out_path),
        "-json",
        "-depth",
        str(depth),
        "-c",
        str(concurrency),
        "-lang",
        lang,
        "-exit-on-inactivity",
        "3m",
    ]
    if extra_reviews:
        argv.append("-extra-reviews")

    # The scraper binary is extremely verbose (per-review Playwright/DOM extraction logs).
    # Without this, subprocess.run() has it inherit our stdout/stderr, which - since this runs
    # inside a FastAPI BackgroundTask - means it floods the uvicorn process's own log output.
    # Redirect it to its own log file instead, next to the results.
    log_path = out_path.with_suffix(".log")
    try:
        with log_path.open("w") as log_file:
            subprocess.run(argv, check=True, timeout=timeout_seconds, stdout=log_file, stderr=subprocess.STDOUT)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"scraper failed, see log at {log_path}") from exc
    finally:
        input_file.unlink(missing_ok=True)

    return out_path


def load_scrape_results(path: Path) -> list[dict]:
    text = path.read_text().strip()
    if not text:
        return []
    # gosom's -json flag writes either a JSON array, or one JSON object per line
    # depending on version — handle both.
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]
