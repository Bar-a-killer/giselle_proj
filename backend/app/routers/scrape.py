from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.config import RAW_SCRAPE_DIR
from app.db import SessionLocal
from app.schemas import ScrapeJobOut, ScrapeRequest
from app.services import jobs
from app.services.embeddings import get_venue_embedder, recompute_venue_embeddings
from app.services.ingest import ingest_entries
from app.services.scraper_runner import ScraperBinaryMissing, load_scrape_results, run_scrape

router = APIRouter(prefix="/api/scrape", tags=["scrape"])

MAX_CONCURRENT_SCRAPE_JOBS = 3


def _run_job(job_id: str, request: ScrapeRequest) -> None:
    jobs.set_running(job_id)
    session = SessionLocal()
    try:
        out_path = RAW_SCRAPE_DIR / f"{job_id}.json"
        run_scrape(
            request.queries,
            out_path,
            depth=request.depth,
            concurrency=request.concurrency,
            extra_reviews=request.extra_reviews,
        )
        entries = load_scrape_results(out_path)
        summary = ingest_entries(entries, session)

        embedder = get_venue_embedder()
        recompute_venue_embeddings(session, embedder, list(summary.touched_venue_ids))

        jobs.set_done(
            job_id,
            {
                "venues_seen": summary.venues_seen,
                "venues_created": summary.venues_created,
                "reviews_seen": summary.reviews_seen,
                "reviews_created": summary.reviews_created,
            },
        )
    except ScraperBinaryMissing as exc:
        jobs.set_error(job_id, str(exc))
    except Exception as exc:  # noqa: BLE001 - surface any failure to the job status
        jobs.set_error(job_id, f"{type(exc).__name__}: {exc}")
    finally:
        session.close()


@router.post("", response_model=ScrapeJobOut, status_code=202)
def start_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    if not request.queries:
        raise HTTPException(status_code=400, detail="at least one query is required")
    job = jobs.try_create_job(MAX_CONCURRENT_SCRAPE_JOBS)
    if job is None:
        raise HTTPException(
            status_code=429,
            detail=f"too many scrapes running already (max {MAX_CONCURRENT_SCRAPE_JOBS} at a time) - wait for one to finish",
        )
    background_tasks.add_task(_run_job, job.id, request)
    return ScrapeJobOut(job_id=job.id, status=job.status)


@router.get("/{job_id}", response_model=ScrapeJobOut)
def get_scrape_status(job_id: str):
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return ScrapeJobOut(job_id=job.id, status=job.status, counts=job.counts, error=job.error)
