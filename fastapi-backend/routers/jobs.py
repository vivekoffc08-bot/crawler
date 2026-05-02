"""
Jobs API router.
Handles /api/jobs/search (POST) and /api/jobs/sources (GET).
Supports both standard JSON response and SSE streaming for live progress.
"""

import asyncio
import json
import time
import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse

from models.job import JobQuery, SearchResponse, JobPosting
from scrapers import SCRAPER_MAP
from utils.dedup import deduplicate_jobs

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/jobs/search", response_model=SearchResponse)
async def search_jobs(query: JobQuery):
    """
    Search for jobs across multiple job boards.
    Runs all selected scrapers concurrently and returns deduplicated results.
    """
    start = time.time()

    # Determine which scrapers to run
    scrapers = []
    if "all" in query.sources:
        scrapers = [cls(query) for cls in SCRAPER_MAP.values()]
    else:
        for source_id in query.sources:
            source_lower = source_id.lower()
            if source_lower in SCRAPER_MAP:
                scrapers.append(SCRAPER_MAP[source_lower](query))

    if not scrapers:
        return SearchResponse(
            query=query,
            total_found=0,
            jobs=[],
            sources_scraped=[],
            scrape_time_seconds=0,
            errors=["No valid sources selected"],
        )

    logger.info(f"Running {len(scrapers)} scrapers: {[s.name for s in scrapers]}")

    # Run all scrapers concurrently with individual timeouts
    async def run_scraper_with_timeout(scraper, timeout=60):
        try:
            return await asyncio.wait_for(scraper.scrape(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"[{scraper.name}] Timed out after {timeout}s")
            raise Exception(f"Timed out after {timeout}s")
        except Exception as e:
            raise

    results = await asyncio.gather(
        *[run_scraper_with_timeout(s) for s in scrapers],
        return_exceptions=True,
    )

    all_jobs: List[JobPosting] = []
    errors: List[str] = []
    sources_scraped: List[str] = []

    for scraper, result in zip(scrapers, results):
        if isinstance(result, Exception):
            error_msg = f"{scraper.name}: {str(result)}"
            errors.append(error_msg)
            logger.error(f"Scraper error — {error_msg}")
        else:
            all_jobs.extend(result)
            sources_scraped.append(scraper.name)
            logger.info(f"[{scraper.name}] returned {len(result)} jobs")

    # Deduplicate and limit results
    final_jobs = deduplicate_jobs(all_jobs)[:query.max_results]

    elapsed = round(time.time() - start, 2)
    logger.info(
        f"Search complete: {len(final_jobs)} unique jobs from {len(sources_scraped)} sources in {elapsed}s"
    )

    return SearchResponse(
        query=query,
        total_found=len(final_jobs),
        jobs=final_jobs,
        sources_scraped=sources_scraped,
        scrape_time_seconds=elapsed,
        errors=errors,
    )


@router.post("/jobs/search/stream")
async def search_jobs_stream(query: JobQuery):
    """
    Stream job search results using Server-Sent Events (SSE).
    Sends progress updates as each scraper completes, then the final results.
    
    Event types:
    - "progress": { source, status, count, message }
    - "result": SearchResponse
    - "error": { source, message }
    """

    async def event_generator():
        start = time.time()

        # Determine scrapers
        scrapers = []
        if "all" in query.sources:
            scrapers = [cls(query) for cls in SCRAPER_MAP.values()]
        else:
            for source_id in query.sources:
                source_lower = source_id.lower()
                if source_lower in SCRAPER_MAP:
                    scrapers.append(SCRAPER_MAP[source_lower](query))

        if not scrapers:
            yield _sse_event("error", {"message": "No valid sources selected"})
            return

        # Send initial progress for all scrapers
        for scraper in scrapers:
            yield _sse_event("progress", {
                "source": scraper.name,
                "status": "pending",
                "count": 0,
                "message": f"Queued {scraper.name}...",
            })

        # Run scrapers concurrently but report results as they come in
        all_jobs: List[JobPosting] = []
        errors: List[str] = []
        sources_scraped: List[str] = []

        # Create tasks
        tasks = {}
        for scraper in scrapers:
            task = asyncio.create_task(
                _run_scraper_safe(scraper),
                name=scraper.name,
            )
            tasks[task] = scraper

            # Signal that scraping has started
            yield _sse_event("progress", {
                "source": scraper.name,
                "status": "scraping",
                "count": 0,
                "message": f"Scraping {scraper.name}...",
            })

        # Collect results as they complete
        for coro in asyncio.as_completed(tasks.keys()):
            task = await _find_completed_task(tasks, coro)
            scraper = tasks.get(task, None)
            scraper_name = scraper.name if scraper else "unknown"

            try:
                result = await coro
                if isinstance(result, list):
                    all_jobs.extend(result)
                    sources_scraped.append(scraper_name)
                    yield _sse_event("progress", {
                        "source": scraper_name,
                        "status": "done",
                        "count": len(result),
                        "message": f"Found {len(result)} jobs on {scraper_name}",
                    })
                else:
                    errors.append(f"{scraper_name}: No results")
                    yield _sse_event("progress", {
                        "source": scraper_name,
                        "status": "error",
                        "count": 0,
                        "message": f"{scraper_name} returned no results",
                    })
            except Exception as e:
                error_msg = f"{scraper_name}: {str(e)}"
                errors.append(error_msg)
                yield _sse_event("progress", {
                    "source": scraper_name,
                    "status": "error",
                    "count": 0,
                    "message": str(e),
                })

        # Deduplicate and send final results
        final_jobs = deduplicate_jobs(all_jobs)[:query.max_results]
        elapsed = round(time.time() - start, 2)

        response = SearchResponse(
            query=query,
            total_found=len(final_jobs),
            jobs=final_jobs,
            sources_scraped=sources_scraped,
            scrape_time_seconds=elapsed,
            errors=errors,
        )

        yield _sse_event("result", response.model_dump(mode="json"))
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _run_scraper_safe(scraper) -> List[JobPosting]:
    """Run a scraper with timeout and exception handling."""
    try:
        return await asyncio.wait_for(scraper.scrape(), timeout=60)
    except asyncio.TimeoutError:
        raise Exception(f"Timed out after 60s")
    except Exception as e:
        raise


async def _find_completed_task(tasks, coro):
    """Find the original task that matches the completed coroutine."""
    for task in tasks:
        if task.done():
            return task
    # Fallback: return first task
    return list(tasks.keys())[0] if tasks else None


def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    json_data = json.dumps(data, default=str)
    return f"event: {event_type}\ndata: {json_data}\n\n"


@router.get("/jobs/sources")
async def get_sources():
    """Return the list of available job sources with metadata."""
    return {
        "sources": [
            {
                "id": "linkedin",
                "name": "LinkedIn",
                "region": "global",
                "logo": "https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png",
                "color": "#0A66C2",
            },
            {
                "id": "indeed",
                "name": "Indeed",
                "region": "global",
                "logo": "https://upload.wikimedia.org/wikipedia/commons/f/fc/Indeed_logo.svg",
                "color": "#2164F3",
            },
            {
                "id": "naukri",
                "name": "Naukri",
                "region": "india",
                "logo": "https://static.naukimg.com/s/4/100/i/naukri_Logo.png",
                "color": "#4A90D9",
            },
            {
                "id": "glassdoor",
                "name": "Glassdoor",
                "region": "global",
                "logo": "https://www.glassdoor.com/favicon.ico",
                "color": "#0CAA41",
            },
            {
                "id": "wellfound",
                "name": "Wellfound",
                "region": "global",
                "logo": "https://wellfound.com/favicon.ico",
                "color": "#000000",
            },
            {
                "id": "internshala",
                "name": "Internshala",
                "region": "india",
                "logo": "https://internshala.com/favicon.ico",
                "color": "#00A5EC",
            },
            {
                "id": "shine",
                "name": "Shine",
                "region": "india",
                "logo": "https://www.shine.com/favicon.ico",
                "color": "#E85D24",
            },
            {
                "id": "monster",
                "name": "Monster India",
                "region": "india",
                "logo": "https://www.monsterindia.com/favicon.ico",
                "color": "#6E45A5",
            },
        ]
    }
